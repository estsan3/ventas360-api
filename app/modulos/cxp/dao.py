"""DAO del módulo cxp."""

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modulos.cxp.models import MovimientoCxp


class CxpDAO:
    def __init__(self, sesion: AsyncSession) -> None:
        self._sesion = sesion

    async def guardar(self, movimiento: MovimientoCxp) -> MovimientoCxp:
        self._sesion.add(movimiento)
        await self._sesion.flush()
        return movimiento

    async def listar_por_proveedor(self, proveedor_id: str) -> list[MovimientoCxp]:
        resultado = await self._sesion.execute(
            select(MovimientoCxp)
            .where(MovimientoCxp.proveedor_id == proveedor_id)
            .order_by(MovimientoCxp.fecha.desc(), MovimientoCxp.creado_en.desc())
        )
        return list(resultado.scalars())

    async def existe_referencia(
        self, referencia_tipo: str, referencia_id: str
    ) -> bool:
        resultado = await self._sesion.execute(
            select(func.count())
            .select_from(MovimientoCxp)
            .where(
                MovimientoCxp.referencia_tipo == referencia_tipo,
                MovimientoCxp.referencia_id == referencia_id,
            )
        )
        return int(resultado.scalar_one()) > 0

    async def totales_proveedor(self, proveedor_id: str) -> tuple[float, float]:
        resultado = await self._sesion.execute(
            select(
                func.coalesce(
                    func.sum(
                        case(
                            (MovimientoCxp.tipo == "debe", MovimientoCxp.monto),
                            else_=0.0,
                        )
                    ),
                    0.0,
                ),
                func.coalesce(
                    func.sum(
                        case(
                            (MovimientoCxp.tipo == "haber", MovimientoCxp.monto),
                            else_=0.0,
                        )
                    ),
                    0.0,
                ),
            ).where(MovimientoCxp.proveedor_id == proveedor_id)
        )
        debe, haber = resultado.one()
        return float(debe), float(haber)

    async def saldos_agrupados(self) -> list[tuple[str, float, float]]:
        resultado = await self._sesion.execute(
            select(
                MovimientoCxp.proveedor_id,
                func.coalesce(
                    func.sum(
                        case(
                            (MovimientoCxp.tipo == "debe", MovimientoCxp.monto),
                            else_=0.0,
                        )
                    ),
                    0.0,
                ),
                func.coalesce(
                    func.sum(
                        case(
                            (MovimientoCxp.tipo == "haber", MovimientoCxp.monto),
                            else_=0.0,
                        )
                    ),
                    0.0,
                ),
            ).group_by(MovimientoCxp.proveedor_id)
        )
        return [(str(r[0]), float(r[1]), float(r[2])) for r in resultado.all()]
