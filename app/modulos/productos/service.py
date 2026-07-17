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
    ProductosPaginaResponse,
)


class ProductosService:
    """Casos de uso de productos."""

    def __init__(self, sesion: AsyncSession) -> None:
        self._sesion = sesion
        self._dao = ProductoDAO(sesion)
        self._bo = ProductoBO()

    async def listar(
        self,
        *,
        q: str | None = None,
        activo: bool | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> ProductosPaginaResponse:
        items, total = await self._dao.listar(
            q=q, activo=activo, page=page, page_size=page_size
        )
        return ProductosPaginaResponse(
            items=[ProductoResponse.model_validate(p) for p in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def obtener(self, producto_id: str) -> ProductoResponse:
        producto = await self._buscar_o_fallar(producto_id)
        return ProductoResponse.model_validate(producto)

    async def crear(self, datos: CrearProductoRequest) -> ProductoResponse:
        existente = await self._dao.buscar_por_sku(datos.sku)
        self._bo.validar_alta(sku_ya_registrado=existente is not None)
        self._bo.validar_stock(datos.stock)
        self._bo.validar_precios(datos.costo, datos.precio)

        producto = Producto(
            sku=datos.sku,
            nombre=datos.nombre,
            marca=datos.marca,
            rubro=datos.rubro,
            codigo_barras=datos.codigo_barras,
            costo=datos.costo,
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

        costo = datos.costo if datos.costo is not None else producto.costo
        precio = datos.precio if datos.precio is not None else producto.precio
        self._bo.validar_precios(costo, precio)

        if datos.nombre is not None:
            producto.nombre = datos.nombre
        if datos.marca is not None:
            producto.marca = datos.marca
        if datos.rubro is not None:
            producto.rubro = datos.rubro
        if datos.codigo_barras is not None:
            producto.codigo_barras = datos.codigo_barras
        if datos.costo is not None:
            producto.costo = datos.costo
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
