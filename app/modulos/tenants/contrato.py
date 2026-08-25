"""Contrato público del módulo tenants."""

from dataclasses import dataclass
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.modulos.tenants.dao import TenantDAO
from app.modulos.tenants.models import Tenant


@dataclass(frozen=True)
class TenantResumen:
    id: str
    slug: str
    nombre: str
    activo: bool


class ContratoTenants(Protocol):
    async def obtener_por_id(self, tenant_id: str) -> TenantResumen | None: ...

    async def obtener_por_slug(self, slug: str) -> TenantResumen | None: ...

    async def existe_tenant(self, tenant_id: str) -> bool: ...


class TenantsLocal:
    def __init__(self, sesion: AsyncSession) -> None:
        self._dao = TenantDAO(sesion)

    async def obtener_por_id(self, tenant_id: str) -> TenantResumen | None:
        tenant = await self._dao.buscar_por_id(tenant_id)
        return None if tenant is None else _resumen(tenant)

    async def obtener_por_slug(self, slug: str) -> TenantResumen | None:
        tenant = await self._dao.buscar_por_slug(slug.strip().lower())
        return None if tenant is None else _resumen(tenant)

    async def existe_tenant(self, tenant_id: str) -> bool:
        tenant = await self._dao.buscar_por_id(tenant_id)
        return tenant is not None and tenant.activo


def _resumen(tenant: Tenant) -> TenantResumen:
    return TenantResumen(
        id=tenant.id,
        slug=tenant.slug,
        nombre=tenant.nombre,
        activo=tenant.activo,
    )
