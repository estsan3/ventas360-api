"""SERVICE del módulo cobranzas."""

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.eventos import EventoDominio, bus_eventos
from app.core.excepciones import RecursoNoEncontrado, ReglaDeNegocioViolada
from app.modulos.bancos.contrato import BancosLocal, ContratoBancos
from app.modulos.caja.contrato import CajaLocal, ContratoCaja
from app.modulos.clientes.contrato import ClientesLocal, ContratoClientes
from app.modulos.cobranzas.bo import CobranzasBO
from app.modulos.cobranzas.dao import CobranzasDAO
from app.modulos.cobranzas.models import ImputacionRecibo, Recibo
from app.modulos.cobranzas.schemas import CrearReciboRequest, ReciboResponse
from app.modulos.cxc.contrato import ContratoCxc, CxcLocal
from app.modulos.ventas.contrato import ContratoVentas, VentasLocal


class CobranzasService:
    def __init__(
        self,
        sesion: AsyncSession,
        clientes: ContratoClientes | None = None,
        cxc: ContratoCxc | None = None,
        ventas: ContratoVentas | None = None,
        caja: ContratoCaja | None = None,
        bancos: ContratoBancos | None = None,
    ) -> None:
        self._sesion = sesion
        self._dao = CobranzasDAO(sesion)
        self._bo = CobranzasBO()
        self._clientes = clientes or ClientesLocal(sesion)
        self._cxc = cxc or CxcLocal(sesion)
        self._ventas = ventas or VentasLocal(sesion)
        self._caja = caja or CajaLocal(sesion)
        self._bancos = bancos or BancosLocal(sesion)

    async def listar(self, cliente_id: str | None = None) -> list[ReciboResponse]:
        items = await self._dao.listar(cliente_id=cliente_id)
        return [ReciboResponse.model_validate(r) for r in items]

    async def obtener(self, recibo_id: str) -> ReciboResponse:
        recibo = await self._dao.buscar_por_id(recibo_id)
        if recibo is None:
            raise RecursoNoEncontrado("Recibo no encontrado")
        return ReciboResponse.model_validate(recibo)

    async def crear(self, datos: CrearReciboRequest) -> ReciboResponse:
        self._bo.validar_medio(datos.medio)
        self._bo.validar_recibo(
            datos.monto, [i.monto for i in datos.imputaciones]
        )

        if not await self._clientes.existe_cliente(datos.cliente_id):
            raise ReglaDeNegocioViolada("Cliente inexistente o inactivo")

        for item in datos.imputaciones:
            factura = await self._ventas.obtener_factura(item.factura_id)
            if factura is None:
                raise ReglaDeNegocioViolada(
                    f"Factura inexistente o no confirmada: {item.factura_id}"
                )
            if factura.cliente_id != datos.cliente_id:
                raise ReglaDeNegocioViolada(
                    "La factura no pertenece al cliente del recibo"
                )

        fecha = datos.fecha or date.today()
        recibo = Recibo(
            cliente_id=datos.cliente_id,
            fecha=fecha,
            monto=round(datos.monto, 2),
            medio=datos.medio,
            observacion=datos.observacion,
            imputaciones=[
                ImputacionRecibo(
                    factura_id=i.factura_id,
                    monto=round(i.monto, 2),
                )
                for i in datos.imputaciones
            ],
        )
        await self._dao.guardar(recibo)

        # Un haber por recibo (referencia única) — reduce saldo CxC.
        await self._cxc.registrar_haber(
            cliente_id=datos.cliente_id,
            monto=datos.monto,
            referencia_tipo="recibo",
            referencia_id=recibo.id,
            concepto=f"Recibo {recibo.id}",
            fecha=fecha,
        )

        # Tesorería (B2/B3): efectivo/tarjeta → caja; transferencia → banco.
        await self._impactar_tesoreria(recibo)

        await self._sesion.commit()
        await self._sesion.refresh(recibo, attribute_names=["imputaciones"])
        await bus_eventos.publicar(
            EventoDominio(
                nombre="cobranzas.recibo.creado",
                datos={
                    "recibo_id": recibo.id,
                    "cliente_id": recibo.cliente_id,
                    "monto": recibo.monto,
                },
            )
        )
        return ReciboResponse.model_validate(recibo)

    async def _impactar_tesoreria(self, recibo: Recibo) -> None:
        concepto = f"Cobranza recibo {recibo.id[:8]}"
        if recibo.medio == "transferencia":
            await self._bancos.acreditar(
                monto=recibo.monto,
                concepto=concepto,
                referencia_tipo="recibo",
                referencia_id=recibo.id,
                fecha=recibo.fecha,
            )
            return
        medio_caja = "tarjeta" if recibo.medio == "tarjeta" else "efectivo"
        await self._caja.registrar_ingreso(
            monto=recibo.monto,
            medio=medio_caja,
            concepto=concepto,
            referencia_tipo="recibo",
            referencia_id=recibo.id,
            fecha=recibo.fecha,
        )
