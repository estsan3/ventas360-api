"""Capa API del m?dulo auth: endpoints HTTP. Sin l?gica de negocio."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import obtener_configuracion
from app.core.database import obtener_sesion
from app.core.dependencias import UsuarioActual, obtener_usuario_actual, requerir_rol
from app.core.seguridad import NOMBRE_COOKIE_ACCESO
from app.modulos.auth.schemas import (
    CrearUsuarioRequest,
    CrearVendedorRequest,
    LoginRequest,
    LoginResponse,
    UsuarioResponse,
)
from app.modulos.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["Autenticaci?n"])

# Router aparte para la gesti?n de usuarios: el front la consume en /usuarios.
router_usuarios = APIRouter(prefix="/usuarios", tags=["Usuarios"])

# Los vendedores son usuarios, pero el front los gestiona desde la pantalla
# de cat?logos (POST/DELETE /catalogos/vendedores). La ruta vive ac? porque
# la entidad pertenece a auth; cat?logos nunca toca usuarios.
router_vendedores = APIRouter(prefix="/catalogos/vendedores", tags=["Usuarios"])

# Alias para inyectar la sesi?n de base de datos en cada endpoint.
Sesion = Annotated[AsyncSession, Depends(obtener_sesion)]


def _setear_cookie_acceso(response: Response, token: str) -> None:
    config = obtener_configuracion()
    response.set_cookie(
        key=NOMBRE_COOKIE_ACCESO,
        value=token,
        httponly=True,
        samesite="lax",
        secure=config.es_produccion,
        max_age=config.jwt_expiracion_minutos * 60,
        path="/",
    )


def _borrar_cookie_acceso(response: Response) -> None:
    config = obtener_configuracion()
    response.delete_cookie(
        key=NOMBRE_COOKIE_ACCESO,
        path="/",
        samesite="lax",
        secure=config.es_produccion,
    )


@router.post("/login", response_model=LoginResponse, operation_id="login")
async def login(
    datos: LoginRequest, sesion: Sesion, response: Response
) -> LoginResponse:
    """Inicia sesi?n: JWT en cookie httpOnly (+ body para clientes API/MCP)."""
    resultado = await AuthService(sesion).login(datos)
    _setear_cookie_acceso(response, resultado.access_token)
    return resultado


@router.get("/me", response_model=UsuarioResponse, operation_id="obtener_perfil")
async def perfil(
    usuario: Annotated[UsuarioActual, Depends(obtener_usuario_actual)],
    sesion: Sesion,
) -> UsuarioResponse:
    """Devuelve el perfil del usuario autenticado (seg?n el token)."""
    return await AuthService(sesion).obtener_usuario(usuario.id)


@router.post("/logout", status_code=204, operation_id="logout")
async def logout(response: Response) -> None:
    """Cierra sesi?n borrando la cookie httpOnly."""
    _borrar_cookie_acceso(response)
    return None


@router_usuarios.get(
    "",
    response_model=list[UsuarioResponse],
    dependencies=[Depends(requerir_rol("administrador"))],
    operation_id="listar_usuarios",
)
async def listar_usuarios(sesion: Sesion) -> list[UsuarioResponse]:
    """Lista los usuarios del backoffice. Solo administradores."""
    return await AuthService(sesion).listar_usuarios()


@router_usuarios.post(
    "",
    response_model=UsuarioResponse,
    status_code=201,
    dependencies=[Depends(requerir_rol("administrador"))],
    operation_id="crear_usuario",
)
async def crear_usuario(datos: CrearUsuarioRequest, sesion: Sesion) -> UsuarioResponse:
    """Da de alta un usuario (administrador o vendedor). Solo administradores."""
    return await AuthService(sesion).crear_usuario(datos)


@router_usuarios.delete(
    "/{usuario_id}",
    status_code=204,
    dependencies=[Depends(requerir_rol("administrador"))],
    operation_id="eliminar_usuario",
)
async def eliminar_usuario(
    usuario_id: str,
    usuario: Annotated[UsuarioActual, Depends(obtener_usuario_actual)],
    sesion: Sesion,
) -> None:
    """Da de baja un usuario. Solo administradores; no permite auto-baja."""
    await AuthService(sesion).eliminar_usuario(usuario_id, solicitante_id=usuario.id)


@router_vendedores.get(
    "",
    response_model=list[UsuarioResponse],
    operation_id="listar_vendedores",
)
async def listar_vendedores(sesion: Sesion) -> list[UsuarioResponse]:
    """Lista vendedores activos (usuarios con rol vendedor)."""
    return await AuthService(sesion).listar_vendedores()


@router_vendedores.post(
    "",
    response_model=UsuarioResponse,
    status_code=201,
    dependencies=[Depends(requerir_rol("administrador"))],
    operation_id="crear_vendedor",
)
async def crear_vendedor(datos: CrearVendedorRequest, sesion: Sesion) -> UsuarioResponse:
    """Alta r?pida de vendedor desde cat?logos. Solo administradores."""
    return await AuthService(sesion).crear_vendedor(datos.nombre)


@router_vendedores.delete(
    "/{usuario_id}",
    status_code=204,
    dependencies=[Depends(requerir_rol("administrador"))],
    operation_id="eliminar_vendedor",
)
async def eliminar_vendedor(
    usuario_id: str,
    usuario: Annotated[UsuarioActual, Depends(obtener_usuario_actual)],
    sesion: Sesion,
) -> None:
    """Baja de un vendedor (usuario con rol vendedor). Solo administradores."""
    await AuthService(sesion).eliminar_usuario(usuario_id, solicitante_id=usuario.id)
