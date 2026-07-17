"""DAO del módulo caja."""

from datetime import date

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modulos.caja.models import MovimientoCaja


class CajaDAO:
    def __init__(self, sesion: AsyncSession) -> None:
        self._sesion = sesion

    async def guardar(self, mov: MovimientoCaja) -> MovimientoCaja:
        self._sesion.add(mov)
        await self._sesion.flush()
        return mov

    async def listar_por_fecha(self, dia: date) -> list[MovimientoCaja]:
        resultado = await self._sesion.execute(
            select(MovimientoCaja)
            .where(MovimientoCaja.fecha == dia)
            .order_by(MovimientoCaja.creado_en.desc())
        )
        return list(resultado.scalars())

    async def existe_referencia(
        self, referencia_tipo: str, referencia_id: str
    ) -> bool:
        if not referencia_id:
            return False
        resultado = await self._sesion.execute(
            select(func.count())
            .select_from(MovimientoCaja)
            .where(
                MovimientoCaja.referencia_tipo == referencia_tipo,
                MovimientoCaja.referencia_id == referencia_id,
            )
        )
        return int(resultado.scalar_one()) > 0

    async def totales_fecha(self, dia: date) -> tuple[float, float]:
        resultado = await self._sesion.execute(
            select(
                func.coalesce(
                    func.sum(
                        case(
                            (MovimientoCaja.tipo == "ingreso", MovimientoCaja.monto),
                            else_=0.0,
                        )
                    ),
                    0.0,
                ),
                func.coalesce(
                    func.sum(
                        case(
                            (MovimientoCaja.tipo == "egreso", MovimientoCaja.monto),
                            else_=0.0,
                        )
                    ),
                    0.0,
                ),
            ).where(MovimientoCaja.fecha == dia)
        )
        ingresos, egresos = resultado.one()
        return float(ingresos), float(egresos)
