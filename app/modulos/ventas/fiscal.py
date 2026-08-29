"""Reglas fiscales ARCA/WSFE (puras: sin DB, sin HTTP)."""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from datetime import date, timedelta

from app.core.excepciones import ReglaDeNegocioViolada


@dataclass(frozen=True)
class IdentidadFiscal:
    letra: str
    cbte_tipo: int
    punto_venta: int
    doc_tipo: int
    doc_nro: str
    cuit_emisor: str
    condicion_iva_receptor: int
    habilitada: bool
    iva_porcentaje: float


CBTE_TIPO = {"A": 1, "B": 6, "C": 11}
DOC_CUIT = 80
DOC_CF = 99

CONDICION_IVA_RECEPTOR = {
    "responsable_inscripto": 1,
    "monotributo": 6,
    "exento": 4,
    "consumidor_final": 5,
}

IVA_ALICUOTA_ID = {
    0.0: 3,
    2.5: 9,
    5.0: 8,
    10.5: 4,
    21.0: 5,
    27.0: 6,
}


def determinar_letra(emisor_iva: str, receptor_iva: str) -> str:
    """Letra AFIP según condición IVA emisor / receptor."""
    if emisor_iva in {"monotributo", "exento"}:
        return "C"
    if receptor_iva == "responsable_inscripto":
        return "A"
    return "B"


def cbte_tipo_de_letra(letra: str) -> int:
    try:
        return CBTE_TIPO[letra]
    except KeyError as exc:
        raise ReglaDeNegocioViolada(f"Letra de comprobante inválida: {letra}") from exc


def documentacion_receptor(condicion_iva: str, cuit: str) -> tuple[int, str]:
    """(DocTipo, DocNro) para WSFE."""
    cuit_limpio = "".join(ch for ch in cuit if ch.isdigit())
    if len(cuit_limpio) == 11:
        return DOC_CUIT, cuit_limpio
    return DOC_CF, "0"


def id_alicuota(iva_porcentaje: float) -> int | None:
    if iva_porcentaje <= 0:
        return None
    clave = round(iva_porcentaje, 1)
    if clave not in IVA_ALICUOTA_ID:
        raise ReglaDeNegocioViolada(f"Alícuota IVA no soportada por ARCA: {iva_porcentaje}")
    return IVA_ALICUOTA_ID[clave]


def condicion_iva_receptor_id(condicion_iva: str) -> int:
    try:
        return CONDICION_IVA_RECEPTOR[condicion_iva]
    except KeyError as exc:
        raise ReglaDeNegocioViolada(
            f"Condición IVA del receptor inválida: {condicion_iva}"
        ) from exc


def validar_emision_fiscal(
    *,
    habilitada: bool,
    cuit_emisor: str,
    punto_venta: int,
    letra: str,
    doc_tipo: int,
    doc_nro: str,
) -> None:
    if not habilitada:
        return
    cuit = "".join(ch for ch in cuit_emisor if ch.isdigit())
    if len(cuit) != 11:
        raise ReglaDeNegocioViolada("Falta el CUIT del emisor para facturar con ARCA")
    if punto_venta < 1:
        raise ReglaDeNegocioViolada("Falta el punto de venta ARCA")
    if letra == "A" and doc_tipo != DOC_CUIT:
        raise ReglaDeNegocioViolada(
            "La Factura A requiere CUIT del cliente (responsable inscripto)"
        )
    if doc_tipo == DOC_CUIT and len("".join(ch for ch in doc_nro if ch.isdigit())) != 11:
        raise ReglaDeNegocioViolada("El CUIT del cliente debe tener 11 dígitos")


def formatear_numero_fiscal(letra: str, punto_venta: int, cbte_nro: int) -> str:
    return f"{letra}-{punto_venta:05d}-{cbte_nro:08d}"


def armar_qr(
    *,
    fecha: date,
    cuit_emisor: str,
    punto_venta: int,
    cbte_tipo: int,
    cbte_nro: int,
    importe: float,
    doc_tipo: int,
    doc_nro: str,
    cae: str,
) -> str:
    payload = {
        "ver": 1,
        "fecha": fecha.isoformat(),
        "cuit": int("".join(ch for ch in cuit_emisor if ch.isdigit()) or "0"),
        "ptoVta": punto_venta,
        "tipoCmp": cbte_tipo,
        "nroCmp": cbte_nro,
        "importe": round(importe, 2),
        "moneda": "PES",
        "ctz": 1,
        "tipoDocRec": doc_tipo,
        "nroDocRec": int("".join(ch for ch in doc_nro if ch.isdigit()) or "0"),
        "tipoCodAut": "E",
        "codAut": int(cae) if cae.isdigit() else 0,
    }
    encoded = base64.b64encode(
        json.dumps(payload, separators=(",", ":")).encode("utf-8")
    ).decode("ascii")
    return f"https://www.afip.gob.ar/fe/qr/?p={encoded}"


def vencimiento_cae(fecha: date, dias: int = 10) -> date:
    return fecha + timedelta(days=dias)


def armar_identidad(
    *,
    habilitada: bool,
    cuit_emisor: str,
    emisor_iva: str,
    punto_venta: int,
    receptor_iva: str,
    cuit_receptor: str,
    iva_porcentaje: float,
) -> IdentidadFiscal:
    letra = determinar_letra(emisor_iva, receptor_iva)
    doc_tipo, doc_nro = documentacion_receptor(receptor_iva, cuit_receptor)
    alicuota = 0.0 if letra == "C" and habilitada else iva_porcentaje
    return IdentidadFiscal(
        letra=letra,
        cbte_tipo=cbte_tipo_de_letra(letra),
        punto_venta=punto_venta,
        doc_tipo=doc_tipo,
        doc_nro=doc_nro,
        cuit_emisor="".join(ch for ch in cuit_emisor if ch.isdigit()),
        condicion_iva_receptor=condicion_iva_receptor_id(receptor_iva),
        habilitada=habilitada,
        iva_porcentaje=alicuota,
    )
