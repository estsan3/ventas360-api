"""DAO del módulo cxc."""

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modulos.cxc.models import MovimientoCxc


class CxcDAO:
    def __init__(self, sesion: AsyncSession) -> None:
        self._sesion = sesion

    async def guardar(self, movimiento: MovimientoCxc) -> MovimientoCxc:
        self._sesion.add(movimiento)
        await self._sesion.flush()
        return movimiento

    async def listar_por_cliente(self, cliente_id: str) -> list[MovimientoCxc]:
        resultado = await self._sesion.execute(
            select(MovimientoCxc)
            .where(MovimientoCxc.cliente_id == cliente_id)
            .order_by(MovimientoCxc.fecha.desc(), MovimientoCxc.creado_en.desc())
        )
        return list(resultado.scalars())

    async def existe_referencia(
        self, referencia_tipo: str, referencia_id: str
    ) -> bool:
        resultado = await self._sesion.execute(
            select(func.count())
            .select_from(MovimientoCxc)
            .where(
                MovimientoCxc.referencia_tipo == referencia_tipo,
                MovimientoCxc.referencia_id == referencia_id,
            )
        )
        return int(resultado.scalar_one()) > 0

    async def totales_cliente(self, cliente_id: str) -> tuple[float, float]:
        resultado = await self._sesion.execute(
            select(
                func.coalesce(
                    func.sum(
                        case(
                            (MovimientoCxc.tipo == "debe", MovimientoCxc.monto),
                            else_=0.0,
                        )
                    ),
                    0.0,
                ),
                func.coalesce(
                    func.sum(
                        case(
                            (MovimientoCxc.tipo == "haber", MovimientoCxc.monto),
                            else_=0.0,
                        )
                    ),
                    0.0,
                ),
            ).where(MovimientoCxc.cliente_id == cliente_id)
        )
        debe, haber = resultado.one()
        return float(debe), float(haber)

    async def saldos_agrupados(
        self,
    ) -> list[tuple[str, float, float, object | None, object | None]]:
        """Lista (cliente_id, debe, haber, fecha_ultimo, fecha_debe_mas_antigua)."""
        resultado = await self._sesion.execute(
            select(
                MovimientoCxc.cliente_id,
                func.coalesce(
                    func.sum(
                        case(
                            (MovimientoCxc.tipo == "debe", MovimientoCxc.monto),
                            else_=0.0,
                        )
                    ),
                    0.0,
                ),
                func.coalesce(
                    func.sum(
                        case(
                            (MovimientoCxc.tipo == "haber", MovimientoCxc.monto),
                            else_=0.0,
                        )
                    ),
                    0.0,
                ),
                func.max(MovimientoCxc.fecha),
                func.min(
                    case(
                        (MovimientoCxc.tipo == "debe", MovimientoCxc.fecha),
                        else_=None,
                    )
                ),
            ).group_by(MovimientoCxc.cliente_id)
        )
        return [
            (str(r[0]), float(r[1]), float(r[2]), r[3], r[4]) for r in resultado.all()
        ]
