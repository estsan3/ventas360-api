"""Capa SERVICE del módulo auth: casos de uso y límites transaccionales.

El service orquesta DAO + BO + infraestructura (tokens) y es el único
lugar donde se hace commit. Los routers solo lo invocan.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.excepciones import RecursoNoEncontrado
from app.core.seguridad import crear_token_acceso, hashear_password
from app.core.tenant_ctx import tenant_id_actual
from app.modulos.auth.bo import UsuarioBO
from app.modulos.auth.dao import UsuarioDAO
from app.modulos.auth.models import Usuario
from app.modulos.auth.schemas import (
    CrearUsuarioRequest,
    LoginRequest,
    LoginResponse,
    UsuarioResponse,
)
from app.modulos.tenants.contrato import ContratoTenants, TenantsLocal


class AuthService:
    """Casos de uso de autenticación y gestión de usuarios."""

    def __init__(
        self,
        sesion: AsyncSession,
        tenants: ContratoTenants | None = None,
    ) -> None:
        self._sesion = sesion
        self._dao = UsuarioDAO(sesion)
        self._bo = UsuarioBO()
        self._tenants = tenants or TenantsLocal(sesion)

    async def login(self, datos: LoginRequest, host: str) -> LoginResponse:
        """Valida credenciales, el Host del comercio y emite un JWT."""
        usuario = await self._dao.buscar_por_email(datos.email)
        self._bo.validar_credenciales(
            usuario.password_hash if usuario else None,
            datos.password,
        )
        assert usuario is not None  # garantizado por validar_credenciales
        await self._exigir_host(usuario, host)

        token = crear_token_acceso(
            subject=usuario.id,
            datos_extra={
                "email": usuario.email,
                "rol": usuario.rol,
                "tenant_id": usuario.tenant_id,
            },
        )
        return LoginResponse(
            access_token=token,
            usuario=await self._con_permisos(usuario),
        )

    async def obtener_perfil(self, usuario_id: str, host: str) -> UsuarioResponse:
        usuario = await self._dao.buscar_por_id(usuario_id)
        if usuario is None:
            raise RecursoNoEncontrado("Usuario no encontrado")
        await self._exigir_host(usuario, host)
        return await self._con_permisos(usuario)

    async def _con_permisos(self, usuario: Usuario) -> UsuarioResponse:
        permisos: list[str] = []
        if usuario.tenant_id:
            permisos = await self._tenants.modulos_habilitados(
                usuario.tenant_id, usuario.rol
            )
        base = UsuarioResponse.model_validate(usuario)
        return base.model_copy(update={"permisos": permisos})

    async def _exigir_host(self, usuario: Usuario, host: str) -> None:
        ctx = await self._tenants.contexto_desde_host(host)
        self._bo.validar_login_host(
            tenant_id_usuario=usuario.tenant_id,
            rol=usuario.rol,
            tipo_host=ctx.tipo,
            tenant_id_host=ctx.tenant_id,
        )

    async def crear_usuario(self, datos: CrearUsuarioRequest) -> UsuarioResponse:
        """Alta de usuario del backoffice."""
        existente = await self._dao.buscar_por_email(datos.email)
        self._bo.validar_alta(email_ya_registrado=existente is not None, rol=datos.rol)

        # El front admin da de alta usuarios sin definirles contraseña:
        # se asigna una inicial conocida hasta implementar la invitación por email.
        password = datos.password or "cambiar12345"
        usuario = Usuario(
            nombre=datos.nombre,
            dni=datos.dni,
            email=datos.email,
            password_hash=hashear_password(password),
            rol=datos.rol,
            tenant_id=tenant_id_actual(),
        )
        await self._dao.guardar(usuario)
        await self._sesion.commit()
        return UsuarioResponse.model_validate(usuario)

    async def listar_usuarios(self) -> list[UsuarioResponse]:
        usuarios = await self._dao.listar()
        return [UsuarioResponse.model_validate(u) for u in usuarios]

    async def listar_vendedores(self) -> list[UsuarioResponse]:
        usuarios = await self._dao.listar_por_rol("vendedor")
        return [UsuarioResponse.model_validate(u) for u in usuarios]

    async def crear_vendedor(self, nombre: str) -> UsuarioResponse:
        """Alta rápida de vendedor (desde catálogos del front).

        Se crea como usuario con rol vendedor y credenciales provisorias;
        cuando tenga que loguearse, un admin le completa email y contraseña.
        """
        import uuid

        sufijo = uuid.uuid4().hex[:8]
        usuario = Usuario(
            nombre=nombre,
            dni="-",
            email=f"vendedor-{sufijo}@pendiente.ventas360",
            password_hash=hashear_password(f"provisoria-{sufijo}"),
            rol="vendedor",
            tenant_id=tenant_id_actual(),
        )
        await self._dao.guardar(usuario)
        await self._sesion.commit()
        return UsuarioResponse.model_validate(usuario)

    async def eliminar_usuario(self, usuario_id: str, solicitante_id: str) -> None:
        """Baja de un usuario del backoffice."""
        usuario = await self._dao.buscar_del_tenant(usuario_id)
        if usuario is None:
            raise RecursoNoEncontrado("Usuario no encontrado")

        administradores = await self._dao.listar_por_rol("administrador")
        self._bo.validar_baja(
            es_el_mismo_usuario=usuario.id == solicitante_id,
            es_ultimo_administrador=(
                usuario.rol == "administrador" and len(administradores) <= 1
            ),
        )
        await self._dao.eliminar(usuario)
        await self._sesion.commit()

    async def obtener_usuario(self, usuario_id: str) -> UsuarioResponse:
        usuario = await self._dao.buscar_por_id(usuario_id)
        if usuario is None:
            raise RecursoNoEncontrado("Usuario no encontrado")
        return UsuarioResponse.model_validate(usuario)
