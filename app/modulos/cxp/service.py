"""Service CxP."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.modulos.cxp.bo import CxpBO
from app.modulos.cxp.dao import CxpDAO
from app.modulos.cxp.schemas import (
    EstadoCuentaProveedorResponse,
    MovimientoCxpResponse,
    SaldoProveedorResponse,
)


class CxpService:
    def __init__(self, sesion: AsyncSession) -> None:
        self._dao = CxpDAO(sesion)
        self._bo = CxpBO()

    async def listar_saldos(self) -> list[SaldoProveedorResponse]:
        filas = await self._dao.saldos_agrupados()
        return [
            SaldoProveedorResponse(
                proveedor_id=pid,
                debe=round(debe, 2),
                haber=round(haber, 2),
                saldo=self._bo.calcular_saldo(debe, haber),
            )
            for pid, debe, haber in filas
        ]

    async def estado_cuenta(self, proveedor_id: str) -> EstadoCuentaProveedorResponse:
        movimientos = await self._dao.listar_por_proveedor(proveedor_id)
        debe, haber = await self._dao.totales_proveedor(proveedor_id)
        return EstadoCuentaProveedorResponse(
            proveedor_id=proveedor_id,
            saldo=self._bo.calcular_saldo(debe, haber),
            movimientos=[MovimientoCxpResponse.model_validate(m) for m in movimientos],
        )
