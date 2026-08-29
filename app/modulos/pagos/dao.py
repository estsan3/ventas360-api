"""DAO del módulo pagos."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.tenant_ctx import del_tenant, es_del_tenant
from app.modulos.pagos.models import PagoProveedor


class PagosDAO:
    def __init__(self, sesion: AsyncSession) -> None:
        self._sesion = sesion

    async def listar(self, proveedor_id: str | None = None) -> list[PagoProveedor]:
        consulta = (
            select(PagoProveedor)
            .options(selectinload(PagoProveedor.lineas))
            .where(del_tenant(PagoProveedor))
            .order_by(PagoProveedor.fecha.desc(), PagoProveedor.id.desc())
        )
        if proveedor_id:
            consulta = consulta.where(PagoProveedor.proveedor_id == proveedor_id)
        return list((await self._sesion.execute(consulta)).scalars())

    async def buscar_por_id(self, pago_id: str) -> PagoProveedor | None:
        resultado = await self._sesion.execute(
            select(PagoProveedor)
            .options(selectinload(PagoProveedor.lineas))
            .where(PagoProveedor.id == pago_id)
        )
        pago = resultado.scalar_one_or_none()
        return pago if es_del_tenant(pago) else None

    async def guardar(self, pago: PagoProveedor) -> PagoProveedor:
        self._sesion.add(pago)
        await self._sesion.flush()
        return pago
