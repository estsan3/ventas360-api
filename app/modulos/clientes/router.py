"""Capa API del módulo clientes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import obtener_sesion
from app.core.dependencias import obtener_usuario_actual, requerir_rol
from app.modulos.clientes.schemas import (
    ActualizarClienteRequest,
    ClienteResponse,
    ClientesPaginaResponse,
    CrearClienteRequest,
)
from app.modulos.clientes.service import ClientesService

router = APIRouter(
    prefix="/clientes",
    tags=["Clientes"],
    dependencies=[Depends(obtener_usuario_actual)],
)

Sesion = Annotated[AsyncSession, Depends(obtener_sesion)]


@router.get(
    "",
    response_model=ClientesPaginaResponse,
    operation_id="listar_clientes",
)
async def listar_clientes(
    sesion: Sesion,
    q: str | None = Query(default=None, description="Busca por nombre, email, teléfono o CUIT"),
    activo: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
) -> ClientesPaginaResponse:
    """Lista clientes con paginación y filtros."""
    return await ClientesService(sesion).listar(
        q=q, activo=activo, page=page, page_size=page_size
    )


@router.get("/{cliente_id}", response_model=ClienteResponse, operation_id="obtener_cliente")
async def obtener_cliente(cliente_id: str, sesion: Sesion) -> ClienteResponse:
    """Obtiene un cliente por ID."""
    return await ClientesService(sesion).obtener(cliente_id)


@router.post(
    "",
    response_model=ClienteResponse,
    status_code=201,
    dependencies=[Depends(requerir_rol("administrador"))],
    operation_id="crear_cliente",
)
async def crear_cliente(datos: CrearClienteRequest, sesion: Sesion) -> ClienteResponse:
    """Alta de cliente. Solo administradores."""
    return await ClientesService(sesion).crear(datos)


@router.put(
    "/{cliente_id}",
    response_model=ClienteResponse,
    dependencies=[Depends(requerir_rol("administrador"))],
    operation_id="actualizar_cliente",
)
async def actualizar_cliente(
    cliente_id: str, datos: ActualizarClienteRequest, sesion: Sesion
) -> ClienteResponse:
    """Actualiza un cliente. Solo administradores."""
    return await ClientesService(sesion).actualizar(cliente_id, datos)


@router.patch(
    "/{cliente_id}/desactivar",
    response_model=ClienteResponse,
    dependencies=[Depends(requerir_rol("administrador"))],
    operation_id="desactivar_cliente",
)
async def desactivar_cliente(cliente_id: str, sesion: Sesion) -> ClienteResponse:
    """Baja lógica de un cliente. Solo administradores."""
    return await ClientesService(sesion).desactivar(cliente_id)
