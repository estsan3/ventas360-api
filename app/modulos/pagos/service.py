"""Service pagos: CxP haber + caja / banco / cartera."""

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.eventos import EventoDominio, bus_eventos
from app.core.excepciones import RecursoNoEncontrado, ReglaDeNegocioViolada
from app.modulos.bancos.contrato import BancosLocal, ContratoBancos
from app.modulos.caja.contrato import CajaLocal, ContratoCaja
from app.modulos.cxp.contrato import ContratoCxp, CxpLocal
from app.modulos.pagos.bo import LineaMedioPago, PagosBO
from app.modulos.pagos.dao import PagosDAO
from app.modulos.pagos.models import LineaPago, PagoProveedor
from app.modulos.pagos.schemas import CrearPagoRequest, PagoResponse
from app.modulos.proveedores.contrato import ContratoProveedores, ProveedoresLocal


class PagosService:
    def __init__(
        self,
        sesion: AsyncSession,
        proveedores: ContratoProveedores | None = None,
        cxp: ContratoCxp | None = None,
        caja: ContratoCaja | None = None,
        bancos: ContratoBancos | None = None,
    ) -> None:
        self._sesion = sesion
        self._dao = PagosDAO(sesion)
        self._bo = PagosBO()
        self._proveedores = proveedores or ProveedoresLocal(sesion)
        self._cxp = cxp or CxpLocal(sesion)
        self._caja = caja or CajaLocal(sesion)
        self._bancos = bancos or BancosLocal(sesion)

    async def listar(self, proveedor_id: str | None = None) -> list[PagoResponse]:
        return [PagoResponse.model_validate(p) for p in await self._dao.listar(proveedor_id)]

    async def obtener(self, pago_id: str) -> PagoResponse:
        pago = await self._dao.buscar_por_id(pago_id)
        if pago is None:
            raise RecursoNoEncontrado("Pago no encontrado")
        return PagoResponse.model_validate(pago)

    async def crear(self, datos: CrearPagoRequest) -> PagoResponse:
        lineas_req = None
        if datos.medios:
            lineas_req = [
                LineaMedioPago(
                    medio=m.medio,
                    monto=round(m.monto, 2),
                    cheque_id=(m.cheque_id or "").strip(),
                    cheque=m.cheque,
                )
                for m in datos.medios
            ]
        lineas = self._bo.normalizar_medios(
            datos.monto, datos.medio, datos.cheque_id, datos.cheque, lineas_req
        )
        medio = self._bo.validar_medios(datos.monto, lineas)

        if not await self._proveedores.existe_proveedor(datos.proveedor_id):
            raise ReglaDeNegocioViolada("Proveedor inexistente o inactivo")

        fecha = datos.fecha or date.today()
        dest = (datos.destinatario or datos.observacion or "Proveedor").strip()
        pago = PagoProveedor(
            proveedor_id=datos.proveedor_id,
            fecha=fecha,
            monto=round(datos.monto, 2),
            medio=medio,
            observacion=datos.observacion,
            lineas=[],
        )
        await self._dao.guardar(pago)

        for linea in lineas:
            cheque_id = await self._impactar_medio(pago, linea, dest)
            pago.lineas.append(
                LineaPago(
                    medio=linea.medio,
                    monto=linea.monto,
                    cheque_id=cheque_id,
                )
            )

        await self._cxp.registrar_haber(
            proveedor_id=datos.proveedor_id,
            monto=datos.monto,
            referencia_tipo="pago_proveedor",
            referencia_id=pago.id,
            concepto=f"Pago {pago.id[:8]}",
            fecha=fecha,
        )

        await self._sesion.commit()
        await self._sesion.refresh(pago, attribute_names=["lineas"])
        await bus_eventos.publicar(
            EventoDominio(
                nombre="pagos.pago.creado",
                datos={
                    "pago_id": pago.id,
                    "proveedor_id": pago.proveedor_id,
                    "monto": pago.monto,
                },
            )
        )
        return PagoResponse.model_validate(pago)

    async def _impactar_medio(
        self, pago: PagoProveedor, linea: LineaMedioPago, destinatario: str
    ) -> str:
        n = len(pago.lineas) + 1
        ref_id = pago.id if n == 1 else f"{pago.id}:{n}"
        concepto = f"Pago proveedor {pago.id[:8]}"
        if linea.medio == "transferencia":
            await self._bancos.debitar(
                monto=linea.monto,
                concepto=concepto,
                referencia_tipo="pago_proveedor",
                referencia_id=ref_id,
                fecha=pago.fecha,
            )
            return ""
        if linea.medio == "efectivo":
            await self._caja.registrar_egreso(
                monto=linea.monto,
                medio="efectivo",
                concepto=concepto,
                referencia_tipo="pago_proveedor",
                referencia_id=ref_id,
                fecha=pago.fecha,
            )
            return ""
        if linea.cheque_id:
            await self._bancos.entregar_cheque(
                linea.cheque_id, destinatario, pago.fecha
            )
            return linea.cheque_id
        assert linea.cheque is not None
        ch = linea.cheque
        valor_id = await self._bancos.emitir_cheque_propio(
            monto=linea.monto,
            numero=ch.numero,
            banco_emisor=ch.banco_emisor,
            destinatario=destinatario,
            fecha=ch.fecha or pago.fecha,
            fecha_vto=ch.fecha_vto,
            observacion=concepto,
        )
        return valor_id
