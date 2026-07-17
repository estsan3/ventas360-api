"""Contrato público del módulo clientes."""

from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.modulos.clientes.dao import ClienteDAO


class ContratoClientes(Protocol):
    """Interfaz que clientes garantiza al resto del sistema."""

    async def contar_activos(self) -> int: ...

    async def existe_cliente(self, cliente_id: str) -> bool: ...


class ClientesLocal:
    """Implementación local del contrato (mismo proceso, misma base)."""

    def __init__(self, sesion: AsyncSession) -> None:
        self._dao = ClienteDAO(sesion)

    async def contar_activos(self) -> int:
        return await self._dao.contar_activos()

    async def existe_cliente(self, cliente_id: str) -> bool:
        cliente = await self._dao.buscar_por_id(cliente_id)
        return cliente is not None and cliente.activo
