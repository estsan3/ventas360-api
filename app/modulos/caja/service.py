"""Service del módulo caja."""

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.modulos.caja.bo import CajaBO
from app.modulos.caja.dao import CajaDAO
from app.modulos.caja.models import MovimientoCaja
from app.modulos.caja.schemas import (
    CrearMovimientoCajaRequest,
    MovimientoCajaResponse,
    SaldoCajaResponse,
)


class CajaService:
    def __init__(self, sesion: AsyncSession) -> None:
        self._sesion = sesion
        self._dao = CajaDAO(sesion)
        self._bo = CajaBO()

    async def listar_movimientos(
        self, dia: date | None = None
    ) -> list[MovimientoCajaResponse]:
        fecha = dia or date.today()
        items = await self._dao.listar_por_fecha(fecha)
        return [MovimientoCajaResponse.model_validate(m) for m in items]

    async def saldo(self, dia: date | None = None) -> SaldoCajaResponse:
        fecha = dia or date.today()
        ingresos, egresos = await self._dao.totales_fecha(fecha)
        return SaldoCajaResponse(
            fecha=fecha,
            ingresos=round(ingresos, 2),
            egresos=round(egresos, 2),
            saldo=self._bo.calcular_saldo(ingresos, egresos),
        )

    async def crear_movimiento(
        self, datos: CrearMovimientoCajaRequest
    ) -> MovimientoCajaResponse:
        self._bo.validar_movimiento(datos.tipo, datos.medio, datos.monto)
        mov = MovimientoCaja(
            fecha=datos.fecha or date.today(),
            tipo=datos.tipo,
            medio=datos.medio,
            monto=round(datos.monto, 2),
            concepto=datos.concepto or f"{datos.tipo} manual",
            referencia_tipo="manual",
            referencia_id="",
        )
        await self._dao.guardar(mov)
        await self._sesion.commit()
        return MovimientoCajaResponse.model_validate(mov)
