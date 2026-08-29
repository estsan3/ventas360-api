"""Contrato público del módulo proveedores."""

from dataclasses import dataclass
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.modulos.proveedores.dao import ProveedorDAO


@dataclass(frozen=True)
class ListaItemResumen:
    id: str
    proveedor_id: str
    codigo_proveedor: str
    nombre: str
    costo: float
    articulo_id: str


class ContratoProveedores(Protocol):
    async def existe_proveedor(self, proveedor_id: str) -> bool: ...

    async def obtener_item(
        self, proveedor_id: str, codigo_proveedor: str
    ) -> ListaItemResumen | None: ...

    async def obtener_item_por_id(self, item_id: str) -> ListaItemResumen | None: ...


class ProveedoresLocal:
    def __init__(self, sesion: AsyncSession) -> None:
        self._dao = ProveedorDAO(sesion)

    async def existe_proveedor(self, proveedor_id: str) -> bool:
        proveedor = await self._dao.buscar_por_id(proveedor_id)
        return proveedor is not None and proveedor.activo

    async def obtener_item(
        self, proveedor_id: str, codigo_proveedor: str
    ) -> ListaItemResumen | None:
        item = await self._dao.buscar_item_por_codigo(proveedor_id, codigo_proveedor)
        return self._a_item(item) if item else None

    async def obtener_item_por_id(self, item_id: str) -> ListaItemResumen | None:
        item = await self._dao.buscar_item(item_id)
        return self._a_item(item) if item else None

    def _a_item(self, item) -> ListaItemResumen:
        return ListaItemResumen(
            id=item.id,
            proveedor_id=item.proveedor_id,
            codigo_proveedor=item.codigo_proveedor,
            nombre=item.nombre,
            costo=item.costo,
            articulo_id=item.articulo_id or "",
        )
