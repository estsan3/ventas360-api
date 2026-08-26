"""DAO del módulo caja."""

from datetime import date

from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant_ctx import del_tenant
from app.modulos.caja.models import MovimientoCaja, SesionCaja


class CajaDAO:
    def __init__(self, sesion: AsyncSession) -> None:
        self._sesion = sesion

    async def guardar(self, mov: MovimientoCaja) -> MovimientoCaja:
        self._sesion.add(mov)
        await self._sesion.flush()
        return mov

    async def listar_por_fecha(self, dia: date) -> list[MovimientoCaja]:
        vigente = await self.buscar_vigente(dia)
        if vigente is None:
            resultado = await self._sesion.execute(
                select(MovimientoCaja)
                .where(del_tenant(MovimientoCaja), MovimientoCaja.fecha == dia)
                .order_by(MovimientoCaja.creado_en.desc())
            )
            return list(resultado.scalars())
        return await self.listar_de_sesion(vigente)

    async def listar_de_sesion(self, caja: SesionCaja) -> list[MovimientoCaja]:
        resultado = await self._sesion.execute(
            select(MovimientoCaja)
            .where(*(await self._filtro_sesion(caja)))
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
                del_tenant(MovimientoCaja),
                MovimientoCaja.referencia_tipo == referencia_tipo,
                MovimientoCaja.referencia_id == referencia_id,
            )
        )
        return int(resultado.scalar_one()) > 0

    async def guardar_sesion(self, sesion: SesionCaja) -> SesionCaja:
        self._sesion.add(sesion)
        await self._sesion.flush()
        return sesion

    async def buscar_abierta(self, dia: date) -> SesionCaja | None:
        resultado = await self._sesion.execute(
            select(SesionCaja).where(
                del_tenant(SesionCaja),
                SesionCaja.fecha == dia,
                SesionCaja.estado == "abierta",
            )
        )
        return resultado.scalar_one_or_none()

    async def buscar_vigente(self, dia: date) -> SesionCaja | None:
        abierta = await self.buscar_abierta(dia)
        if abierta is not None:
            return abierta
        resultado = await self._sesion.execute(
            select(SesionCaja)
            .where(del_tenant(SesionCaja), SesionCaja.fecha == dia)
            .order_by(SesionCaja.abierta_en.desc())
            .limit(1)
        )
        return resultado.scalar_one_or_none()

    async def es_primera_sesion(self, caja: SesionCaja) -> bool:
        resultado = await self._sesion.execute(
            select(func.count())
            .select_from(SesionCaja)
            .where(
                del_tenant(SesionCaja),
                SesionCaja.fecha == caja.fecha,
                SesionCaja.abierta_en < caja.abierta_en,
            )
        )
        return int(resultado.scalar_one()) == 0

    async def _filtro_sesion(self, caja: SesionCaja) -> list:
        base = [del_tenant(MovimientoCaja), MovimientoCaja.fecha == caja.fecha]
        if await self.es_primera_sesion(caja):
            return [
                *base,
                or_(
                    MovimientoCaja.sesion_id == caja.id,
                    MovimientoCaja.sesion_id == "",
                ),
            ]
        return [*base, MovimientoCaja.sesion_id == caja.id]

    async def totales_fecha(
        self, dia: date, *, medio: str | None = None
    ) -> tuple[float, float]:
        vigente = await self.buscar_vigente(dia)
        if vigente is not None:
            return await self.totales_sesion(vigente, medio=medio)
        filtro = [del_tenant(MovimientoCaja), MovimientoCaja.fecha == dia]
        if medio:
            filtro.append(MovimientoCaja.medio == medio)
        return await self._sumar(filtro)

    async def totales_sesion(
        self, caja: SesionCaja, *, medio: str | None = None
    ) -> tuple[float, float]:
        filtro = await self._filtro_sesion(caja)
        if medio:
            filtro.append(MovimientoCaja.medio == medio)
        return await self._sumar(filtro)

    async def _sumar(self, filtro: list) -> tuple[float, float]:
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
            ).where(*filtro)
        )
        ingresos, egresos = resultado.one()
        return float(ingresos), float(egresos)
