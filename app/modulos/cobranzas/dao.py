"""DAO del módulo cobranzas."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modulos.cobranzas.models import Recibo


class CobranzasDAO:
    def __init__(self, sesion: AsyncSession) -> None:
        self._sesion = sesion

    async def listar(self, cliente_id: str | None = None) -> list[Recibo]:
        consulta = (
            select(Recibo)
            .options(selectinload(Recibo.imputaciones))
            .order_by(Recibo.fecha.desc(), Recibo.id.desc())
        )
        if cliente_id:
            consulta = consulta.where(Recibo.cliente_id == cliente_id)
        return list((await self._sesion.execute(consulta)).scalars())

    async def buscar_por_id(self, recibo_id: str) -> Recibo | None:
        resultado = await self._sesion.execute(
            select(Recibo)
            .options(selectinload(Recibo.imputaciones))
            .where(Recibo.id == recibo_id)
        )
        return resultado.scalar_one_or_none()

    async def guardar(self, recibo: Recibo) -> Recibo:
        self._sesion.add(recibo)
        await self._sesion.flush()
        return recibo
