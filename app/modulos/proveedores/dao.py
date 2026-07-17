"""DAO del módulo proveedores."""

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.paginacion import calcular_offset
from app.modulos.proveedores.models import Proveedor


class ProveedorDAO:
    def __init__(self, sesion: AsyncSession) -> None:
        self._sesion = sesion

    async def listar(
        self,
        *,
        q: str | None = None,
        activo: bool | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Proveedor], int]:
        filtros = []
        if activo is not None:
            filtros.append(Proveedor.activo.is_(activo))
        if q:
            termino = f"%{q.strip()}%"
            filtros.append(
                or_(
                    Proveedor.nombre.ilike(termino),
                    Proveedor.email.ilike(termino),
                    Proveedor.cuit.ilike(termino),
                )
            )

        consulta_total = select(func.count()).select_from(Proveedor)
        consulta = select(Proveedor).order_by(Proveedor.nombre)
        if filtros:
            consulta_total = consulta_total.where(*filtros)
            consulta = consulta.where(*filtros)

        total = int((await self._sesion.execute(consulta_total)).scalar_one())
        resultado = await self._sesion.execute(
            consulta.offset(calcular_offset(page, page_size)).limit(page_size)
        )
        return list(resultado.scalars()), total

    async def buscar_por_id(self, proveedor_id: str) -> Proveedor | None:
        return await self._sesion.get(Proveedor, proveedor_id)

    async def guardar(self, proveedor: Proveedor) -> Proveedor:
        self._sesion.add(proveedor)
        await self._sesion.flush()
        return proveedor
