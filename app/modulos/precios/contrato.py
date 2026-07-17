"""Contrato público del módulo precios."""

from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.excepciones import RecursoNoEncontrado
from app.modulos.precios.dao import PreciosDAO
from app.modulos.productos.contrato import ContratoProductos, ProductosLocal


class ContratoPrecios(Protocol):
    async def obtener_precio(
        self, articulo_id: str, cliente_id: str | None = None
    ) -> float: ...


class PreciosLocal:
    """Resuelve precio: override de lista default → precio de catálogo."""

    def __init__(
        self,
        sesion: AsyncSession,
        productos: ContratoProductos | None = None,
    ) -> None:
        self._dao = PreciosDAO(sesion)
        self._productos = productos or ProductosLocal(sesion)

    async def obtener_precio(
        self, articulo_id: str, cliente_id: str | None = None
    ) -> float:
        # cliente_id reservado para listas por cliente (Fase B).
        _ = cliente_id
        producto = await self._productos.obtener_producto(articulo_id)
        if producto is None or not producto.activo:
            raise RecursoNoEncontrado("Artículo no encontrado")

        lista = await self._dao.buscar_lista_default()
        if lista is not None:
            override = await self._dao.buscar_precio(lista.id, articulo_id)
            if override is not None:
                return override.precio
        return producto.precio
