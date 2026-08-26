"""Contrato público del módulo tenants."""

from dataclasses import dataclass
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import obtener_configuracion
from app.modulos.tenants.bo import TIPO_PLATAFORMA, TIPO_SIN_SLUG, TenantsBO
from app.modulos.tenants.dao import TenantDAO
from app.modulos.tenants.models import Tenant


@dataclass(frozen=True)
class TenantResumen:
    id: str
    slug: str
    nombre: str
    activo: bool


@dataclass(frozen=True)
class ContextoHostResumen:
    """Clasificación del Host/Origin para login y autorización."""

    tipo: str
    slug: str | None
    tenant_id: str | None


class ContratoTenants(Protocol):
    async def obtener_por_id(self, tenant_id: str) -> TenantResumen | None: ...

    async def obtener_por_slug(self, slug: str) -> TenantResumen | None: ...

    async def existe_tenant(self, tenant_id: str) -> bool: ...

    async def contexto_desde_host(self, host: str) -> ContextoHostResumen: ...

    async def modulos_habilitados(self, tenant_id: str, rol: str) -> list[str]: ...


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

    async def contexto_desde_host(self, host: str) -> ContextoHostResumen:
        bo = TenantsBO()
        tipo, slug = bo.clasificar_host(host, obtener_configuracion().slug_plataforma)
        if tipo == TIPO_PLATAFORMA:
            return ContextoHostResumen(tipo="plataforma", slug=None, tenant_id=None)
        if tipo == TIPO_SIN_SLUG or slug is None:
            return ContextoHostResumen(tipo="sin_slug", slug=None, tenant_id=None)
        tenant = await self._dao.buscar_por_slug(slug)
        if tenant is None or not tenant.activo:
            return ContextoHostResumen(tipo="comercio", slug=slug, tenant_id=None)
        return ContextoHostResumen(tipo="comercio", slug=slug, tenant_id=tenant.id)

    async def modulos_habilitados(self, tenant_id: str, rol: str) -> list[str]:
        filas = await self._dao.listar_permisos(tenant_id)
        por_rol = {p.modulo: p.habilitado for p in filas if p.rol == rol}
        return TenantsBO().resolver_modulos(rol, por_rol or None)


def _resumen(tenant: Tenant) -> TenantResumen:
    return TenantResumen(
        id=tenant.id,
        slug=tenant.slug,
        nombre=tenant.nombre,
        activo=tenant.activo,
    )
