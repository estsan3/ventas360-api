"""Capa DAO del módulo auth: acceso a datos, sin lógica de negocio."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant_ctx import del_tenant, es_del_tenant
from app.modulos.auth.models import Usuario


class UsuarioDAO:
    """Operaciones de persistencia sobre la tabla `auth_usuario`."""

    def __init__(self, sesion: AsyncSession) -> None:
        self._sesion = sesion

    async def buscar_por_email(self, email: str) -> Usuario | None:
        """Busca un usuario por email (único global). Login no tiene tenant."""
        resultado = await self._sesion.execute(
            select(Usuario).where(Usuario.email == email)
        )
        return resultado.scalar_one_or_none()

    async def buscar_por_id(self, usuario_id: str) -> Usuario | None:
        """Busca por ID sin filtrar tenant (`/me` y login)."""
        return await self._sesion.get(Usuario, usuario_id)

    async def buscar_del_tenant(self, usuario_id: str) -> Usuario | None:
        """Usuario del comercio actual; None si es de otro tenant (404)."""
        usuario = await self.buscar_por_id(usuario_id)
        return usuario if es_del_tenant(usuario) else None

    async def listar(self) -> list[Usuario]:
        resultado = await self._sesion.execute(
            select(Usuario).where(del_tenant(Usuario)).order_by(Usuario.nombre)
        )
        return list(resultado.scalars())

    async def listar_por_rol(self, rol: str) -> list[Usuario]:
        resultado = await self._sesion.execute(
            select(Usuario)
            .where(del_tenant(Usuario), Usuario.rol == rol)
            .order_by(Usuario.nombre)
        )
        return list(resultado.scalars())

    async def listar_por_tenant_id(self, tenant_id: str) -> list[Usuario]:
        """Usuarios de un comercio (plataforma; no usa el tenant del request)."""
        resultado = await self._sesion.execute(
            select(Usuario)
            .where(Usuario.tenant_id == tenant_id)
            .order_by(Usuario.rol, Usuario.nombre)
        )
        return list(resultado.scalars())

    async def listar_administradores_de_tenants(
        self, tenant_ids: list[str]
    ) -> list[Usuario]:
        if not tenant_ids:
            return []
        resultado = await self._sesion.execute(
            select(Usuario)
            .where(
                Usuario.tenant_id.in_(tenant_ids),
                Usuario.rol == "administrador",
            )
            .order_by(Usuario.nombre)
        )
        return list(resultado.scalars())

    async def eliminar(self, usuario: Usuario) -> None:
        """Elimina el usuario de la sesión. El commit lo hace la capa service."""
        await self._sesion.delete(usuario)
        await self._sesion.flush()

    async def guardar(self, usuario: Usuario) -> Usuario:
        """Agrega el usuario a la sesión. El commit lo hace la capa service."""
        self._sesion.add(usuario)
        await self._sesion.flush()
        return usuario

    async def contar(self) -> int:
        """Cantidad de usuarios del comercio actual."""
        resultado = await self._sesion.execute(
            select(func.count()).select_from(Usuario).where(del_tenant(Usuario))
        )
        return int(resultado.scalar_one())
