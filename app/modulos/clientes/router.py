"""Capa API del módulo clientes."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import obtener_sesion
from app.core.dependencias import obtener_usuario_actual, requerir_rol
from app.modulos.clientes.schemas import (
    ActualizarClienteRequest,
    ClienteResponse,
    CrearClienteRequest,
)
from app.modulos.clientes.service import ClientesService

router = APIRouter(
    prefix="/clientes",
    tags=["Clientes"],
    dependencies=[Depends(obtener_usuario_actual)],
)

Sesion = Annotated[AsyncSession, Depends(obtener_sesion)]


@router.get("", response_model=list[ClienteResponse], operation_id="listar_clientes")
async def listar_clientes(sesion: Sesion) -> list[ClienteResponse]:
    """Lista todos los clientes."""
    return await ClientesService(sesion).listar()


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
