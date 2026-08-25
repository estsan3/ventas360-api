"""Contrato público del módulo auth.

Otros módulos (ej: catálogos, para componer administradores y vendedores
en su respuesta agregada) consumen SOLO esta interfaz, nunca los
DAO/models internos.
"""

from dataclasses import dataclass
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.seguridad import hashear_password
from app.modulos.auth.bo import UsuarioBO
from app.modulos.auth.dao import UsuarioDAO
from app.modulos.auth.models import Usuario

_PASSWORD_INICIAL = "cambiar12345"


@dataclass(frozen=True)
class UsuarioResumen:
    """Datos mínimos de un usuario que otros módulos necesitan conocer."""

    id: str
    nombre: str
    rol: str


@dataclass(frozen=True)
class AdministradorInicial:
    """Primer administrador de un comercio (alta de plataforma)."""

    id: str
    nombre: str
    email: str
    rol: str


class ContratoAuth(Protocol):
    """Interfaz que auth garantiza al resto del sistema."""

    async def listar_por_rol(self, rol: str) -> list[UsuarioResumen]:
        """Usuarios activos con el rol dado (ej: 'vendedor')."""
        ...

    async def existe_usuario(self, usuario_id: str) -> bool:
        """True si el usuario existe (activo o no)."""
        ...

    async def crear_administrador_inicial(
        self,
        *,
        tenant_id: str,
        nombre: str,
        dni: str,
        email: str,
        password: str | None,
    ) -> AdministradorInicial:
        """Alta del primer admin del comercio. Sin commit."""
        ...


class AuthLocal:
    """Implementación local del contrato (mismo proceso, misma base)."""

    def __init__(self, sesion: AsyncSession) -> None:
        self._dao = UsuarioDAO(sesion)
        self._bo = UsuarioBO()

    async def listar_por_rol(self, rol: str) -> list[UsuarioResumen]:
        usuarios = await self._dao.listar_por_rol(rol)
        return [UsuarioResumen(id=u.id, nombre=u.nombre, rol=u.rol) for u in usuarios]

    async def existe_usuario(self, usuario_id: str) -> bool:
        return await self._dao.buscar_del_tenant(usuario_id) is not None

    async def crear_administrador_inicial(
        self,
        *,
        tenant_id: str,
        nombre: str,
        dni: str,
        email: str,
        password: str | None,
    ) -> AdministradorInicial:
        existente = await self._dao.buscar_por_email(email)
        self._bo.validar_alta(
            email_ya_registrado=existente is not None,
            rol="administrador",
        )
        usuario = Usuario(
            nombre=nombre.strip(),
            dni=dni.strip(),
            email=email,
            password_hash=hashear_password(password or _PASSWORD_INICIAL),
            rol="administrador",
            tenant_id=tenant_id,
        )
        await self._dao.guardar(usuario)
        return AdministradorInicial(
            id=usuario.id,
            nombre=usuario.nombre,
            email=usuario.email,
            rol=usuario.rol,
        )
