"""DAO del módulo zonas."""

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.paginacion import calcular_offset
from app.modulos.zonas.models import Zona


class ZonaDAO:
    def __init__(self, sesion: AsyncSession) -> None:
        self._sesion = sesion

    async def listar(
        self,
        *,
        q: str | None = None,
        activo: bool | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Zona], int]:
        filtros = []
        if activo is not None:
            filtros.append(Zona.activo.is_(activo))
        if q:
            termino = f"%{q.strip()}%"
            filtros.append(
                or_(Zona.nombre.ilike(termino), Zona.codigo.ilike(termino))
            )

        consulta_total = select(func.count()).select_from(Zona)
        consulta = select(Zona).order_by(Zona.nombre)
        if filtros:
            consulta_total = consulta_total.where(*filtros)
            consulta = consulta.where(*filtros)

        total = int((await self._sesion.execute(consulta_total)).scalar_one())
        resultado = await self._sesion.execute(
            consulta.offset(calcular_offset(page, page_size)).limit(page_size)
        )
        return list(resultado.scalars()), total

    async def buscar_por_id(self, zona_id: str) -> Zona | None:
        return await self._sesion.get(Zona, zona_id)

    async def buscar_por_nombre(self, nombre: str) -> Zona | None:
        resultado = await self._sesion.execute(
            select(Zona).where(func.lower(Zona.nombre) == nombre.strip().lower())
        )
        return resultado.scalar_one_or_none()

    async def guardar(self, zona: Zona) -> Zona:
        self._sesion.add(zona)
        await self._sesion.flush()
        return zona
