"""Contrato público del módulo clientes."""

from dataclasses import dataclass
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.modulos.clientes.dao import ClienteDAO


@dataclass(frozen=True)
class ClienteResumen:
    id: str
    nombre: str


class ContratoClientes(Protocol):
    """Interfaz que clientes garantiza al resto del sistema."""

    async def contar_activos(self) -> int: ...

    async def nombres_por_ids(self, ids: list[str]) -> dict[str, str]: ...

    async def existe_cliente(self, cliente_id: str) -> bool: ...

    async def buscar_por_texto(self, q: str, *, limite: int = 10) -> list[ClienteResumen]: ...


class ClientesLocal:
    """Implementación local del contrato (mismo proceso, misma base)."""

    def __init__(self, sesion: AsyncSession) -> None:
        self._dao = ClienteDAO(sesion)

    async def contar_activos(self) -> int:
        return await self._dao.contar_activos()

    async def nombres_por_ids(self, ids: list[str]) -> dict[str, str]:
        return await self._dao.nombres_por_ids(ids)

    async def existe_cliente(self, cliente_id: str) -> bool:
        cliente = await self._dao.buscar_por_id(cliente_id)
        return cliente is not None and cliente.activo

    async def buscar_por_texto(self, q: str, *, limite: int = 10) -> list[ClienteResumen]:
        items, _ = await self._dao.listar(q=q, activo=True, page=1, page_size=limite)
        return [ClienteResumen(id=c.id, nombre=c.nombre) for c in items]
