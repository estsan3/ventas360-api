"""Capa API del módulo productos."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import obtener_sesion
from app.core.dependencias import obtener_usuario_actual, requerir_rol
from app.modulos.productos.schemas import (
    ActualizarProductoRequest,
    CrearProductoRequest,
    ProductoResponse,
    ProductosPaginaResponse,
)
from app.modulos.productos.service import ProductosService

router = APIRouter(
    prefix="/productos",
    tags=["Productos"],
    dependencies=[Depends(obtener_usuario_actual)],
)

Sesion = Annotated[AsyncSession, Depends(obtener_sesion)]


@router.get(
    "",
    response_model=ProductosPaginaResponse,
    operation_id="listar_productos",
)
async def listar_productos(
    sesion: Sesion,
    q: str | None = Query(
        default=None, description="Busca por SKU, nombre, código de barras, marca o rubro"
    ),
    activo: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
) -> ProductosPaginaResponse:
    """Lista productos con paginación y búsqueda."""
    return await ProductosService(sesion).listar(
        q=q, activo=activo, page=page, page_size=page_size
    )


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
