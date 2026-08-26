"""DAO del módulo compras."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.tenant_ctx import del_tenant, es_del_tenant
from app.modulos.compras.models import Compra


class ComprasDAO:
    def __init__(self, sesion: AsyncSession) -> None:
        self._sesion = sesion

    async def listar(self, tipo: str | None = None) -> list[Compra]:
        consulta = (
            select(Compra)
            .options(selectinload(Compra.lineas))
            .where(del_tenant(Compra))
            .order_by(Compra.fecha.desc(), Compra.id.desc())
        )
        if tipo:
            consulta = consulta.where(Compra.tipo == tipo)
        return list((await self._sesion.execute(consulta)).scalars())

    async def buscar_por_id(self, compra_id: str) -> Compra | None:
        resultado = await self._sesion.execute(
            select(Compra)
            .options(selectinload(Compra.lineas))
            .where(Compra.id == compra_id)
        )
        compra = resultado.scalar_one_or_none()
        return compra if es_del_tenant(compra) else None

    async def guardar(self, compra: Compra) -> Compra:
        self._sesion.add(compra)
        await self._sesion.flush()
        return compra
