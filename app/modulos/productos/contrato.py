"""Contrato público del módulo productos."""

from dataclasses import dataclass
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.modulos.productos.dao import ProductoDAO


@dataclass(frozen=True)
class ProductoResumen:
    """Datos mínimos de un producto para otros módulos."""

    id: str
    sku: str
    nombre: str
    precio: float
    stock: int
    activo: bool


class ContratoProductos(Protocol):
    """Interfaz que productos garantiza al resto del sistema."""

    async def contar_activos(self) -> int: ...

    async def stock_total(self) -> int: ...

    async def obtener_producto(self, producto_id: str) -> ProductoResumen | None: ...


class ProductosLocal:
    """Implementación local del contrato (mismo proceso, misma base)."""

    def __init__(self, sesion: AsyncSession) -> None:
        self._dao = ProductoDAO(sesion)

    async def contar_activos(self) -> int:
        return await self._dao.contar_activos()

    async def stock_total(self) -> int:
        return await self._dao.stock_total()

    async def obtener_producto(self, producto_id: str) -> ProductoResumen | None:
        producto = await self._dao.buscar_por_id(producto_id)
        if producto is None:
            return None
        return ProductoResumen(
            id=producto.id,
            sku=producto.sku,
            nombre=producto.nombre,
            precio=producto.precio,
            stock=producto.stock,
            activo=producto.activo,
        )
