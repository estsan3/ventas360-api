"""Capa API del módulo productos."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import obtener_sesion
from app.core.dependencias import obtener_usuario_actual, requerir_rol
from app.modulos.productos.schemas import (
    ActualizarProductoRequest,
    CrearProductoRequest,
    ProductoResponse,
)
from app.modulos.productos.service import ProductosService

router = APIRouter(
    prefix="/productos",
    tags=["Productos"],
    dependencies=[Depends(obtener_usuario_actual)],
)

Sesion = Annotated[AsyncSession, Depends(obtener_sesion)]


@router.get("", response_model=list[ProductoResponse], operation_id="listar_productos")
async def listar_productos(sesion: Sesion) -> list[ProductoResponse]:
    """Lista todos los productos."""
    return await ProductosService(sesion).listar()


@router.get("/{producto_id}", response_model=ProductoResponse, operation_id="obtener_producto")
async def obtener_producto(producto_id: str, sesion: Sesion) -> ProductoResponse:
    """Obtiene un producto por ID."""
    return await ProductosService(sesion).obtener(producto_id)


@router.post(
    "",
    response_model=ProductoResponse,
    status_code=201,
    dependencies=[Depends(requerir_rol("administrador"))],
    operation_id="crear_producto",
)
async def crear_producto(datos: CrearProductoRequest, sesion: Sesion) -> ProductoResponse:
    """Alta de producto. Solo administradores."""
    return await ProductosService(sesion).crear(datos)


@router.put(
    "/{producto_id}",
    response_model=ProductoResponse,
    dependencies=[Depends(requerir_rol("administrador"))],
    operation_id="actualizar_producto",
)
async def actualizar_producto(
    producto_id: str, datos: ActualizarProductoRequest, sesion: Sesion
) -> ProductoResponse:
    """Actualiza un producto. Solo administradores."""
    return await ProductosService(sesion).actualizar(producto_id, datos)
