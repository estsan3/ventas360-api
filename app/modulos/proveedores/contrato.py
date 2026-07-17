"""Contrato público del módulo proveedores."""

from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.modulos.proveedores.dao import ProveedorDAO


class ContratoProveedores(Protocol):
    async def existe_proveedor(self, proveedor_id: str) -> bool: ...


class ProveedoresLocal:
    def __init__(self, sesion: AsyncSession) -> None:
        self._dao = ProveedorDAO(sesion)

    async def existe_proveedor(self, proveedor_id: str) -> bool:
        proveedor = await self._dao.buscar_por_id(proveedor_id)
        return proveedor is not None and proveedor.activo
