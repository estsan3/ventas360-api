"""SERVICE del módulo tenants."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import obtener_configuracion
from app.core.excepciones import RecursoNoEncontrado, ReglaDeNegocioViolada
from app.core.tenant_ctx import tenant_id_actual, usando_tenant
from app.modulos.auth.contrato import AuthLocal, ContratoAuth, UsuarioDeTenant
from app.modulos.tenants.bo import (
    MODULOS_MATRIZ,
    ROLES_EDITABLES,
    TIPO_PLATAFORMA,
    TIPO_SIN_SLUG,
    TenantsBO,
)
from app.modulos.tenants.dao import TenantDAO
from app.modulos.tenants.models import PermisoRol, Tenant
from app.modulos.tenants.schemas import (
    ActualizarPermisosRequest,
    ActualizarTenantRequest,
    AdministradorCreadoResponse,
    CambiarPasswordUsuarioRequest,
    CeldaPermisoResponse,
    ContextoHostResponse,
    CrearTenantRequest,
    MatrizPermisosResponse,
    TenantCreadoResponse,
    TenantDetalleResponse,
    TenantPublico,
    TenantResponse,
    TenantUsuarioResponse,
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
        admins = await self._auth.primeros_administradores([t.id for t in tenants])
        return [self._a_respuesta(t, admins.get(t.id)) for t in tenants]

    async def obtener(self, tenant_id: str) -> TenantDetalleResponse:
        tenant = await self._buscar_o_fallar(tenant_id)
        usuarios = await self._auth.listar_usuarios_de_tenant(tenant_id)
        admin = next((u for u in usuarios if u.rol == "administrador"), None)
        return TenantDetalleResponse(
            **self._a_respuesta(tenant, admin).model_dump(),
            usuarios=[
                TenantUsuarioResponse(
                    id=u.id,
                    nombre=u.nombre,
                    email=u.email,
                    dni=u.dni,
                    rol=u.rol,
                )
                for u in usuarios
            ],
        )

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
        with usando_tenant(tenant.id):
            await self.asegurar_permisos_default(tenant.id)
        await self._sesion.commit()
        return TenantCreadoResponse(
            id=tenant.id,
            slug=tenant.slug,
            nombre=tenant.nombre,
            activo=tenant.activo,
            admin_nombre=creado.nombre,
            admin_email=creado.email,
            admin_dni=creado.dni,
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
        admins = await self._auth.primeros_administradores([tenant.id])
        return self._a_respuesta(tenant, admins.get(tenant.id))

    async def asegurar_permisos_default(self, tenant_id: str) -> None:
        """Escribe la matriz default si el comercio aún no tiene filas. Sin commit."""
        existentes = await self._dao.listar_permisos(tenant_id)
        if existentes:
            return
        for rol in ROLES_EDITABLES:
            for modulo, _etiqueta, vend, enc in self._bo.celdas_default():
                habilitado = vend if rol == "vendedor" else enc
                await self._dao.guardar_permiso(
                    PermisoRol(
                        tenant_id=tenant_id,
                        rol=rol,
                        modulo=modulo,
                        habilitado=habilitado,
                    )
                )

    async def modulos_habilitados(self, tenant_id: str, rol: str) -> list[str]:
        filas = await self._dao.listar_permisos(tenant_id)
        por_rol = {p.modulo: p.habilitado for p in filas if p.rol == rol}
        return self._bo.resolver_modulos(rol, por_rol or None)

    async def obtener_matriz(self) -> MatrizPermisosResponse:
        tenant_id = tenant_id_actual()
        filas = await self._dao.listar_permisos(tenant_id)
        if not filas:
            await self.asegurar_permisos_default(tenant_id)
            await self._sesion.commit()
            filas = await self._dao.listar_permisos(tenant_id)
        vend = {p.modulo: p.habilitado for p in filas if p.rol == "vendedor"}
        enc = {p.modulo: p.habilitado for p in filas if p.rol == "encargado"}
        items = []
        for modulo, etiqueta, def_v, def_e in self._bo.celdas_default():
            items.append(
                CeldaPermisoResponse(
                    modulo=modulo,
                    etiqueta=etiqueta,
                    vendedor=vend.get(modulo, def_v),
                    encargado=enc.get(modulo, def_e),
                    administrador=True,
                )
            )
        return MatrizPermisosResponse(items=items)

    async def actualizar_permisos(
        self, datos: ActualizarPermisosRequest
    ) -> MatrizPermisosResponse:
        self._bo.validar_actualizacion_permisos(datos.rol, datos.modulos)
        tenant_id = tenant_id_actual()
        await self.asegurar_permisos_default(tenant_id)
        for modulo in MODULOS_MATRIZ:
            habilitado = datos.modulos.get(modulo, False)
            existente = await self._dao.buscar_permiso(tenant_id, datos.rol, modulo)
            if existente is None:
                await self._dao.guardar_permiso(
                    PermisoRol(
                        tenant_id=tenant_id,
                        rol=datos.rol,
                        modulo=modulo,
                        habilitado=habilitado,
                    )
                )
            else:
                existente.habilitado = habilitado
                await self._dao.guardar_permiso(existente)
        await self._sesion.commit()
        return await self.obtener_matriz()

    async def cambiar_password_usuario(
        self, tenant_id: str, usuario_id: str, datos: CambiarPasswordUsuarioRequest
    ) -> TenantUsuarioResponse:
        await self._buscar_o_fallar(tenant_id)
        usuario = await self._auth.cambiar_password_de_tenant(
            tenant_id, usuario_id, datos.password
        )
        await self._sesion.commit()
        return TenantUsuarioResponse(
            id=usuario.id,
            nombre=usuario.nombre,
            email=usuario.email,
            dni=usuario.dni,
            rol=usuario.rol,
        )

    def _a_respuesta(
        self, tenant: Tenant, admin: UsuarioDeTenant | None
    ) -> TenantResponse:
        admin_nombre = admin.nombre if admin is not None else None
        admin_email = admin.email if admin is not None else None
        admin_dni = admin.dni if admin is not None else None
        return TenantResponse(
            id=tenant.id,
            slug=tenant.slug,
            nombre=tenant.nombre,
            activo=tenant.activo,
            admin_nombre=admin_nombre,
            admin_email=admin_email,
            admin_dni=admin_dni,
        )

    async def _buscar_o_fallar(self, tenant_id: str) -> Tenant:
        tenant = await self._dao.buscar_por_id(tenant_id)
        if tenant is None:
            raise RecursoNoEncontrado("Comercio no encontrado")
        return tenant
