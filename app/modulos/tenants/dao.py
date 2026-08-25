"""DAO del módulo tenants."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modulos.tenants.models import PermisoRol, Tenant


class TenantDAO:
    def __init__(self, sesion: AsyncSession) -> None:
        self._sesion = sesion

    async def buscar_por_id(self, tenant_id: str) -> Tenant | None:
        return await self._sesion.get(Tenant, tenant_id)

    async def buscar_por_slug(self, slug: str) -> Tenant | None:
        resultado = await self._sesion.execute(
            select(Tenant).where(Tenant.slug == slug)
        )
        return resultado.scalar_one_or_none()

    async def listar(self, *, solo_activos: bool = False) -> list[Tenant]:
        consulta = select(Tenant).order_by(Tenant.nombre)
        if solo_activos:
            consulta = consulta.where(Tenant.activo.is_(True))
        resultado = await self._sesion.execute(consulta)
        return list(resultado.scalars())

    async def guardar(self, tenant: Tenant) -> Tenant:
        self._sesion.add(tenant)
        await self._sesion.flush()
        return tenant

    async def listar_permisos(self, tenant_id: str) -> list[PermisoRol]:
        resultado = await self._sesion.execute(
            select(PermisoRol)
            .where(PermisoRol.tenant_id == tenant_id)
            .order_by(PermisoRol.rol, PermisoRol.modulo)
        )
        return list(resultado.scalars())

    async def buscar_permiso(
        self, tenant_id: str, rol: str, modulo: str
    ) -> PermisoRol | None:
        resultado = await self._sesion.execute(
            select(PermisoRol).where(
                PermisoRol.tenant_id == tenant_id,
                PermisoRol.rol == rol,
                PermisoRol.modulo == modulo,
            )
        )
        return resultado.scalar_one_or_none()

    async def guardar_permiso(self, permiso: PermisoRol) -> PermisoRol:
        self._sesion.add(permiso)
        await self._sesion.flush()
        return permiso
