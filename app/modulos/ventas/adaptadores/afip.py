"""Adaptador real hacia ARCA/AFIP: WSAA + WSFE (SOAP).

Requisitos:
1. Certificado digital + clave privada (WSASS en homologación).
2. Alta del servicio `wsfe` asociada al certificado.
3. Variables `VENTAS360_AFIP_*` apuntando a esos archivos.
"""

from __future__ import annotations

import html
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

import httpx

from app.core.config import Configuracion
from app.modulos.ventas.adaptadores.wsaa import TicketAcceso, obtener_ticket
from app.modulos.ventas.puerto import ProveedorFE, ResultadoFE, SolicitudFE

WSFE_HOMO = "https://wswhomo.afip.gov.ar/wsfev1/service.asmx"
WSFE_PROD = "https://servicios1.afip.gov.ar/wsfev1/service.asmx"
NS = "http://ar.gov.afip.dif.FEV1/"
SOAP_ACTION = "http://ar.gov.afip.dif.FEV1/{operacion}"


class AdaptadorAfip(ProveedorFE):
    """Implementación real vía WSAA + WSFE SOAP."""

    def __init__(
        self,
        ruta_certificado: str,
        ruta_clave_privada: str,
        homologacion: bool = True,
        cliente: httpx.AsyncClient | None = None,
    ) -> None:
        self._certificado = Path(ruta_certificado)
        self._clave = Path(ruta_clave_privada)
        self._homologacion = homologacion
        self._cliente = cliente
        self._ticket: TicketAcceso | None = None
        self._url = WSFE_HOMO if homologacion else WSFE_PROD

    @classmethod
    def desde_config(cls, cfg: Configuracion) -> AdaptadorAfip:
        return cls(
            ruta_certificado=cfg.afip_certificado,
            ruta_clave_privada=cfg.afip_clave_privada,
            homologacion=cfg.afip_homologacion,
        )

    def _validar_archivos(self) -> str | None:
        if not self._certificado.is_file():
            return f"No existe el certificado ARCA: {self._certificado}"
        if not self._clave.is_file():
            return f"No existe la clave privada ARCA: {self._clave}"
        return None

    async def ultimo_autorizado(
        self, *, cuit_emisor: str, punto_venta: int, cbte_tipo: int
    ) -> int:
        error_cfg = self._validar_archivos()
        if error_cfg:
            raise RuntimeError(error_cfg)
        ticket = await self._obtener_ticket()
        inner = (
            _auth_xml(ticket, cuit_emisor)
            + f"<PtoVta>{punto_venta}</PtoVta><CbteTipo>{cbte_tipo}</CbteTipo>"
        )
        xml = await self._post("FECompUltimoAutorizado", inner)
        if _es_fault(xml):
            raise RuntimeError(_faultstring(xml))
        nro = _texto(xml, "CbteNro")
        try:
            return int(nro or "0")
        except ValueError:
            return 0

    async def solicitar_cae(self, solicitud: SolicitudFE) -> ResultadoFE:
        error_cfg = self._validar_archivos()
        if error_cfg:
            return ResultadoFE(autorizada=False, error=error_cfg)
        try:
            ticket = await self._obtener_ticket()
            xml = await self._post("FECAESolicitar", _armar_fecae(ticket, solicitud))
            return parsear_cae(xml, solicitud.cbte_nro)
        except Exception as exc:
            return ResultadoFE(autorizada=False, error=str(exc))

    async def _obtener_ticket(self) -> TicketAcceso:
        if self._ticket and self._ticket.vigente():
            return self._ticket
        self._ticket = await obtener_ticket(
            certificado=self._certificado,
            clave=self._clave,
            homologacion=self._homologacion,
            service="wsfe",
            cliente=self._cliente,
        )
        return self._ticket

    async def _post(self, operacion: str, inner: str) -> str:
        body = (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
            'xmlns:xsd="http://www.w3.org/2001/XMLSchema">'
            "<soap:Body>"
            f'<{operacion} xmlns="{NS}">{inner}</{operacion}>'
            "</soap:Body></soap:Envelope>"
        )
        propio = self._cliente is None
        http = self._cliente or httpx.AsyncClient(
            timeout=60.0, verify=not self._homologacion
        )
        try:
            resp = await http.post(
                self._url,
                content=body.encode("utf-8"),
                headers={
                    "Content-Type": "text/xml; charset=utf-8",
                    "SOAPAction": f'"{SOAP_ACTION.format(operacion=operacion)}"',
                },
            )
            return resp.text
        finally:
            if propio:
                await http.aclose()


def _auth_xml(ticket: TicketAcceso, cuit: str) -> str:
    return (
        f"<Auth><Token>{ticket.token}</Token><Sign>{ticket.sign}</Sign>"
        f"<Cuit>{cuit}</Cuit></Auth>"
    )


def _monto(valor: float) -> str:
    return f"{valor:.2f}"


def _armar_fecae(ticket: TicketAcceso, s: SolicitudFE) -> str:
    iva_xml = ""
    if s.iva_id is not None and s.imp_iva > 0:
        iva_xml = (
            "<Iva><AlicIva>"
            f"<Id>{s.iva_id}</Id>"
            f"<BaseImp>{_monto(s.imp_neto)}</BaseImp>"
            f"<Importe>{_monto(s.imp_iva)}</Importe>"
            "</AlicIva></Iva>"
        )
    return (
        _auth_xml(ticket, s.cuit_emisor)
        + "<FeCAEReq><FeCabReq>"
        "<CantReg>1</CantReg>"
        f"<PtoVta>{s.punto_venta}</PtoVta>"
        f"<CbteTipo>{s.cbte_tipo}</CbteTipo>"
        "</FeCabReq><FeDetReq><FECAEDetRequest>"
        f"<Concepto>{s.concepto}</Concepto>"
        f"<DocTipo>{s.doc_tipo}</DocTipo>"
        f"<DocNro>{s.doc_nro}</DocNro>"
        f"<CbteDesde>{s.cbte_nro}</CbteDesde>"
        f"<CbteHasta>{s.cbte_nro}</CbteHasta>"
        f"<CbteFch>{s.fecha.strftime('%Y%m%d')}</CbteFch>"
        f"<ImpTotal>{_monto(s.imp_total)}</ImpTotal>"
        f"<ImpTotConc>{_monto(s.imp_tot_conc)}</ImpTotConc>"
        f"<ImpNeto>{_monto(s.imp_neto)}</ImpNeto>"
        "<ImpOpEx>0.00</ImpOpEx><ImpTrib>0.00</ImpTrib>"
        f"<ImpIVA>{_monto(s.imp_iva)}</ImpIVA>"
        f"<MonId>{s.moneda}</MonId>"
        f"<MonCotiz>{s.cotizacion}</MonCotiz>"
        f"<CondicionIVAReceptorId>{s.condicion_iva_receptor}</CondicionIVAReceptorId>"
        f"{iva_xml}"
        "</FECAEDetRequest></FeDetReq></FeCAEReq>"
    )


def _texto(xml: str, tag: str) -> str:
    try:
        raiz = ET.fromstring(xml)
    except ET.ParseError:
        return ""
    for elem in raiz.iter():
        if elem.tag.rsplit("}", 1)[-1] == tag and elem.text:
            return elem.text.strip()
    return ""


def _textos(xml: str, tag: str) -> list[str]:
    try:
        raiz = ET.fromstring(xml)
    except ET.ParseError:
        return []
    return [
        (elem.text or "").strip()
        for elem in raiz.iter()
        if elem.tag.rsplit("}", 1)[-1] == tag and elem.text
    ]


def _es_fault(xml: str) -> bool:
    compacto = xml.lower()
    return "<faultstring>" in compacto or ":fault>" in compacto


def _faultstring(xml: str) -> str:
    texto = html.unescape(xml)
    inicio = texto.lower().find("<faultstring>")
    fin = texto.lower().find("</faultstring>")
    if inicio >= 0 and fin > inicio:
        return texto[inicio + len("<faultstring>") : fin].strip()
    return "Error SOAP de WSFE"


def parsear_cae(xml: str, cbte_nro: int) -> ResultadoFE:
    if _es_fault(xml) and "CAE" not in xml:
        return ResultadoFE(autorizada=False, error=_faultstring(xml))
    errores = _errores_wsfe(xml)
    cae = _texto(xml, "CAE")
    vto = _texto(xml, "CAEFchVto")
    resultado = _texto(xml, "Resultado")
    if resultado == "R" or (errores and not cae):
        return ResultadoFE(autorizada=False, error=errores or "ARCA rechazó el comprobante")
    if not cae:
        return ResultadoFE(
            autorizada=False,
            error=errores or _faultstring(xml) or "WSFE no devolvió CAE",
        )
    vencimiento = None
    if vto:
        try:
            vencimiento = datetime.strptime(vto, "%Y%m%d").date()
        except ValueError:
            vencimiento = None
    return ResultadoFE(
        autorizada=True,
        cae=cae,
        cae_vencimiento=vencimiento,
        cbte_nro=cbte_nro,
        error=errores,
    )


def _errores_wsfe(xml: str) -> str:
    msgs = _textos(xml, "Msg")
    codes = _textos(xml, "Code")
    partes: list[str] = []
    if msgs:
        for i, msg in enumerate(msgs):
            codigo = codes[i] if i < len(codes) else ""
            partes.append(f"{codigo}: {msg}".strip(": "))
    return " | ".join(partes)
