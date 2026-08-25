"""SERVICE del módulo tenants."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import obtener_configuracion
from app.core.excepciones import RecursoNoEncontrado, ReglaDeNegocioViolada
from app.modulos.auth.contrato import AuthLocal, ContratoAuth
from app.modulos.tenants.bo import TIPO_PLATAFORMA, TIPO_SIN_SLUG, TenantsBO
from app.modulos.tenants.dao import TenantDAO
from app.modulos.tenants.models import Tenant
from app.modulos.tenants.schemas import (
    ActualizarTenantRequest,
    AdministradorCreadoResponse,
    ContextoHostResponse,
    CrearTenantRequest,
    TenantCreadoResponse,
    TenantPublico,
    TenantResponse,
)


class TenantsService:
    def __init__(
        self,
        sesion: AsyncSession,
        auth: ContratoAuth | None = None,
    ) -> None:
        self._sesion = sesion
        self._dao = TenantDAO(sesion)
        self._bo = TenantsBO()
        self._auth = auth or AuthLocal(sesion)

    async def contexto_desde_host(self, host: str) -> ContextoHostResponse:
        """Clasifica el Host/Origin y, si hay slug de comercio, busca el tenant."""
        slug_plataforma = obtener_configuracion().slug_plataforma
        tipo, slug = self._bo.clasificar_host(host, slug_plataforma)
        if tipo == TIPO_PLATAFORMA:
            return ContextoHostResponse(tipo="plataforma")
        if tipo == TIPO_SIN_SLUG or slug is None:
            return ContextoHostResponse(tipo="sin_slug")

        tenant = await self._dao.buscar_por_slug(slug)
        if tenant is None or not tenant.activo:
            return ContextoHostResponse(tipo="comercio", slug=slug, tenant=None)
        return ContextoHostResponse(
            tipo="comercio",
            slug=slug,
            tenant=TenantPublico.model_validate(tenant),
        )

    async def listar(self) -> list[TenantResponse]:
        tenants = await self._dao.listar()
        return [TenantResponse.model_validate(t) for t in tenants]

    async def obtener(self, tenant_id: str) -> TenantResponse:
        tenant = await self._buscar_o_fallar(tenant_id)
        return TenantResponse.model_validate(tenant)

    async def obtener_por_slug(self, slug: str) -> TenantResponse:
        normalizado = self._bo.normalizar_slug(slug)
        tenant = await self._dao.buscar_por_slug(normalizado)
        if tenant is None or not tenant.activo:
            raise RecursoNoEncontrado("Comercio no encontrado")
        return TenantResponse.model_validate(tenant)

    async def crear(self, datos: CrearTenantRequest) -> TenantCreadoResponse:
        """Alta de comercio y su primer administrador (una transacción)."""
        self._bo.validar_nombre(datos.nombre)
        slug = self._bo.validar_slug(
            datos.slug, obtener_configuracion().slug_plataforma
        )
        if await self._dao.buscar_por_slug(slug) is not None:
            raise ReglaDeNegocioViolada("Ya existe un comercio con ese slug")

        tenant = Tenant(slug=slug, nombre=datos.nombre.strip())
        await self._dao.guardar(tenant)

        admin = datos.administrador
        creado = await self._auth.crear_administrador_inicial(
            tenant_id=tenant.id,
            nombre=admin.nombre,
            dni=admin.dni,
            email=str(admin.email),
            password=admin.password,
        )
        await self._sesion.commit()
        return TenantCreadoResponse(
            id=tenant.id,
            slug=tenant.slug,
            nombre=tenant.nombre,
            activo=tenant.activo,
            administrador=AdministradorCreadoResponse(
                id=creado.id,
                nombre=creado.nombre,
                email=creado.email,
                rol=creado.rol,
            ),
        )

    async def actualizar(
        self, tenant_id: str, datos: ActualizarTenantRequest
    ) -> TenantResponse:
        tenant = await self._buscar_o_fallar(tenant_id)
        if datos.nombre is not None:
            self._bo.validar_nombre(datos.nombre)
            tenant.nombre = datos.nombre.strip()
        if datos.activo is not None:
            tenant.activo = datos.activo
        await self._dao.guardar(tenant)
        await self._sesion.commit()
        return TenantResponse.model_validate(tenant)

    async def _buscar_o_fallar(self, tenant_id: str) -> Tenant:
        tenant = await self._dao.buscar_por_id(tenant_id)
        if tenant is None:
            raise RecursoNoEncontrado("Comercio no encontrado")
        return tenant
