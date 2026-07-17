"""Capa DAO del módulo productos."""

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.paginacion import calcular_offset
from app.modulos.productos.models import Producto


class ProductoDAO:
    """Persistencia de productos."""

    def __init__(self, sesion: AsyncSession) -> None:
        self._sesion = sesion

    async def listar(
        self,
        *,
        q: str | None = None,
        activo: bool | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Producto], int]:
        filtros = []
        if activo is not None:
            filtros.append(Producto.activo.is_(activo))
        if q:
            termino = f"%{q.strip()}%"
            filtros.append(
                or_(
                    Producto.sku.ilike(termino),
                    Producto.nombre.ilike(termino),
                    Producto.codigo_barras.ilike(termino),
                    Producto.marca.ilike(termino),
                    Producto.rubro.ilike(termino),
                )
            )

        consulta_total = select(func.count()).select_from(Producto)
        consulta = select(Producto).order_by(Producto.nombre)
        if filtros:
            consulta_total = consulta_total.where(*filtros)
            consulta = consulta.where(*filtros)

        total = int((await self._sesion.execute(consulta_total)).scalar_one())
        resultado = await self._sesion.execute(
            consulta.offset(calcular_offset(page, page_size)).limit(page_size)
        )
        return list(resultado.scalars()), total

    async def buscar_por_id(self, producto_id: str) -> Producto | None:
        return await self._sesion.get(Producto, producto_id)

    async def buscar_por_sku(self, sku: str) -> Producto | None:
        resultado = await self._sesion.execute(
            select(Producto).where(Producto.sku == sku)
        )
        return resultado.scalar_one_or_none()

    async def guardar(self, producto: Producto) -> Producto:
        self._sesion.add(producto)
        await self._sesion.flush()
        return producto

    async def listar_activos(self) -> list[Producto]:
        resultado = await self._sesion.execute(
            select(Producto)
            .where(Producto.activo.is_(True))
            .order_by(Producto.nombre)
        )
        return list(resultado.scalars())

    async def contar_activos(self) -> int:
        resultado = await self._sesion.execute(
            select(func.count()).select_from(Producto).where(Producto.activo.is_(True))
        )
        return int(resultado.scalar_one())

    async def stock_total(self) -> int:
        resultado = await self._sesion.execute(
            select(func.coalesce(func.sum(Producto.stock), 0)).where(
                Producto.activo.is_(True)
            )
        )
        return int(resultado.scalar_one())
