"""Capa DAO del módulo productos."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modulos.productos.models import Producto


class ProductoDAO:
    """Persistencia de productos."""

    def __init__(self, sesion: AsyncSession) -> None:
        self._sesion = sesion

    async def listar(self) -> list[Producto]:
        resultado = await self._sesion.execute(select(Producto).order_by(Producto.nombre))
        return list(resultado.scalars())

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

    async def contar_activos(self) -> int:
        resultado = await self._sesion.execute(
            select(func.count()).select_from(Producto).where(Producto.activo.is_(True))
        )
        return int(resultado.scalar_one())

    async def stock_total(self) -> int:
        resultado = await self._sesion.execute(
            select(func.coalesce(func.sum(Producto.stock), 0)).where(Producto.activo.is_(True))
        )
        return int(resultado.scalar_one())
