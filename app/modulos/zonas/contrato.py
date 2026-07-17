"""Contrato público del módulo zonas."""

from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.modulos.zonas.dao import ZonaDAO


class ContratoZonas(Protocol):
    async def existe_zona(self, zona_id: str) -> bool: ...


class ZonasLocal:
    def __init__(self, sesion: AsyncSession) -> None:
        self._dao = ZonaDAO(sesion)

    async def existe_zona(self, zona_id: str) -> bool:
        zona = await self._dao.buscar_por_id(zona_id)
        return zona is not None and zona.activo
