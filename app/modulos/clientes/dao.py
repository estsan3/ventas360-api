"""Capa DAO del módulo clientes."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modulos.clientes.models import Cliente


class ClienteDAO:
    """Persistencia de clientes."""

    def __init__(self, sesion: AsyncSession) -> None:
        self._sesion = sesion

    async def listar(self, solo_activos: bool = False) -> list[Cliente]:
        consulta = select(Cliente).order_by(Cliente.nombre)
        if solo_activos:
            consulta = consulta.where(Cliente.activo.is_(True))
        resultado = await self._sesion.execute(consulta)
        return list(resultado.scalars())

    async def buscar_por_id(self, cliente_id: str) -> Cliente | None:
        return await self._sesion.get(Cliente, cliente_id)

    async def buscar_por_email(self, email: str) -> Cliente | None:
        resultado = await self._sesion.execute(
            select(Cliente).where(Cliente.email == email)
        )
        return resultado.scalar_one_or_none()

    async def guardar(self, cliente: Cliente) -> Cliente:
        self._sesion.add(cliente)
        await self._sesion.flush()
        return cliente

    async def contar_activos(self) -> int:
        resultado = await self._sesion.execute(
            select(func.count()).select_from(Cliente).where(Cliente.activo.is_(True))
        )
        return int(resultado.scalar_one())
