"""Capa SERVICE del módulo productos."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.excepciones import RecursoNoEncontrado
from app.modulos.productos.bo import ProductoBO
from app.modulos.productos.dao import ProductoDAO
from app.modulos.productos.models import Producto
from app.modulos.productos.schemas import (
    ActualizarProductoRequest,
    CrearProductoRequest,
    ProductoResponse,
)


class ProductosService:
    """Casos de uso de productos."""

    def __init__(self, sesion: AsyncSession) -> None:
        self._sesion = sesion
        self._dao = ProductoDAO(sesion)
        self._bo = ProductoBO()

    async def listar(self) -> list[ProductoResponse]:
        productos = await self._dao.listar()
        return [ProductoResponse.model_validate(p) for p in productos]

    async def obtener(self, producto_id: str) -> ProductoResponse:
        producto = await self._buscar_o_fallar(producto_id)
        return ProductoResponse.model_validate(producto)

    async def crear(self, datos: CrearProductoRequest) -> ProductoResponse:
        existente = await self._dao.buscar_por_sku(datos.sku)
        self._bo.validar_alta(sku_ya_registrado=existente is not None)
        self._bo.validar_stock(datos.stock)

        producto = Producto(
            sku=datos.sku,
            nombre=datos.nombre,
            precio=datos.precio,
            stock=datos.stock,
        )
        await self._dao.guardar(producto)
        await self._sesion.commit()
        return ProductoResponse.model_validate(producto)

    async def actualizar(
        self, producto_id: str, datos: ActualizarProductoRequest
    ) -> ProductoResponse:
        producto = await self._buscar_o_fallar(producto_id)

        if datos.sku is not None and datos.sku != producto.sku:
            existente = await self._dao.buscar_por_sku(datos.sku)
            self._bo.validar_alta(sku_ya_registrado=existente is not None)
            producto.sku = datos.sku
        if datos.nombre is not None:
            producto.nombre = datos.nombre
        if datos.precio is not None:
            producto.precio = datos.precio
        if datos.stock is not None:
            self._bo.validar_stock(datos.stock)
            producto.stock = datos.stock
        if datos.activo is not None:
            producto.activo = datos.activo

        await self._sesion.commit()
        return ProductoResponse.model_validate(producto)

    async def _buscar_o_fallar(self, producto_id: str) -> Producto:
        producto = await self._dao.buscar_por_id(producto_id)
        if producto is None:
            raise RecursoNoEncontrado("Producto no encontrado")
        return producto
