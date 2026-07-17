"""SERVICE del módulo cxc."""


from sqlalchemy.ext.asyncio import AsyncSession

from app.core.excepciones import ReglaDeNegocioViolada
from app.modulos.clientes.contrato import ClientesLocal, ContratoClientes
from app.modulos.cxc.bo import CxcBO
from app.modulos.cxc.contrato import CxcLocal
from app.modulos.cxc.dao import CxcDAO
from app.modulos.cxc.schemas import (
    EstadoCuentaResponse,
    MovimientoCxcResponse,
    RegistrarMovimientoRequest,
    SaldoClienteResponse,
)


class CxcService:
    def __init__(
        self,
        sesion: AsyncSession,
        clientes: ContratoClientes | None = None,
    ) -> None:
        self._sesion = sesion
        self._dao = CxcDAO(sesion)
        self._bo = CxcBO()
        self._clientes = clientes or ClientesLocal(sesion)
        self._local = CxcLocal(sesion)

    async def estado_cuenta(self, cliente_id: str) -> EstadoCuentaResponse:
        await self._asegurar_cliente(cliente_id)
        movimientos = await self._dao.listar_por_cliente(cliente_id)
        debe, haber = await self._dao.totales_cliente(cliente_id)
        return EstadoCuentaResponse(
            cliente_id=cliente_id,
            saldo=self._bo.calcular_saldo(debe, haber),
            movimientos=[MovimientoCxcResponse.model_validate(m) for m in movimientos],
        )

    async def saldo(self, cliente_id: str) -> SaldoClienteResponse:
        await self._asegurar_cliente(cliente_id)
        debe, haber = await self._dao.totales_cliente(cliente_id)
        movimientos = await self._dao.listar_por_cliente(cliente_id)
        fecha_ultimo = max((m.fecha for m in movimientos), default=None)
        fecha_debe = min(
            (m.fecha for m in movimientos if m.tipo == "debe"),
            default=None,
        )
        return SaldoClienteResponse(
            cliente_id=cliente_id,
            saldo=self._bo.calcular_saldo(debe, haber),
            debe_total=round(debe, 2),
            haber_total=round(haber, 2),
            fecha_ultimo_movimiento=fecha_ultimo,
            fecha_debe_mas_antigua=fecha_debe,
        )

    async def listar_saldos(self) -> list[SaldoClienteResponse]:
        filas = await self._dao.saldos_agrupados()
        return [
            SaldoClienteResponse(
                cliente_id=cliente_id,
                saldo=self._bo.calcular_saldo(debe, haber),
                debe_total=round(debe, 2),
                haber_total=round(haber, 2),
                fecha_ultimo_movimiento=fecha_ultimo,
                fecha_debe_mas_antigua=fecha_debe,
            )
            for cliente_id, debe, haber, fecha_ultimo, fecha_debe in filas
        ]

    async def registrar_ajuste(
        self, datos: RegistrarMovimientoRequest
    ) -> MovimientoCxcResponse:
        await self._asegurar_cliente(datos.cliente_id)
        if datos.tipo == "debe":
            await self._local.registrar_debe(
                datos.cliente_id,
                datos.monto,
                "ajuste",
                "",
                datos.concepto,
                datos.fecha,
            )
        else:
            await self._local.registrar_haber(
                datos.cliente_id,
                datos.monto,
                "ajuste",
                "",
                datos.concepto,
                datos.fecha,
            )
        await self._sesion.commit()
        movimientos = await self._dao.listar_por_cliente(datos.cliente_id)
        return MovimientoCxcResponse.model_validate(movimientos[0])

    async def _asegurar_cliente(self, cliente_id: str) -> None:
        if not await self._clientes.existe_cliente(cliente_id):
            raise ReglaDeNegocioViolada("Cliente inexistente o inactivo")
