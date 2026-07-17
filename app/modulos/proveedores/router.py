"""API del módulo proveedores."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import obtener_sesion
from app.core.dependencias import obtener_usuario_actual, requerir_rol
from app.modulos.proveedores.schemas import (
    ActualizarProveedorRequest,
    CrearProveedorRequest,
    ProveedorResponse,
    ProveedoresPaginaResponse,
)
from app.modulos.proveedores.service import ProveedoresService

router = APIRouter(
    prefix="/proveedores",
    tags=["Proveedores"],
    dependencies=[Depends(obtener_usuario_actual)],
)

Sesion = Annotated[AsyncSession, Depends(obtener_sesion)]


@router.get("", response_model=ProveedoresPaginaResponse, operation_id="listar_proveedores")
async def listar_proveedores(
    sesion: Sesion,
    q: str | None = Query(default=None),
    activo: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
) -> ProveedoresPaginaResponse:
    return await ProveedoresService(sesion).listar(
        q=q, activo=activo, page=page, page_size=page_size
    )


@router.get(
    "/{proveedor_id}",
    response_model=ProveedorResponse,
    operation_id="obtener_proveedor",
)
async def obtener_proveedor(proveedor_id: str, sesion: Sesion) -> ProveedorResponse:
    return await ProveedoresService(sesion).obtener(proveedor_id)


@router.post(
    "",
    response_model=ProveedorResponse,
    status_code=201,
    dependencies=[Depends(requerir_rol("administrador"))],
    operation_id="crear_proveedor",
)
async def crear_proveedor(
    datos: CrearProveedorRequest, sesion: Sesion
) -> ProveedorResponse:
    return await ProveedoresService(sesion).crear(datos)


@router.put(
    "/{proveedor_id}",
    response_model=ProveedorResponse,
    dependencies=[Depends(requerir_rol("administrador"))],
    operation_id="actualizar_proveedor",
)
async def actualizar_proveedor(
    proveedor_id: str, datos: ActualizarProveedorRequest, sesion: Sesion
) -> ProveedorResponse:
    return await ProveedoresService(sesion).actualizar(proveedor_id, datos)


@router.patch(
    "/{proveedor_id}/desactivar",
    response_model=ProveedorResponse,
    dependencies=[Depends(requerir_rol("administrador"))],
    operation_id="desactivar_proveedor",
)
async def desactivar_proveedor(proveedor_id: str, sesion: Sesion) -> ProveedorResponse:
    return await ProveedoresService(sesion).desactivar(proveedor_id)
