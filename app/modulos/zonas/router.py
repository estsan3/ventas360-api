"""API del módulo zonas."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import obtener_sesion
from app.core.dependencias import obtener_usuario_actual, requerir_rol
from app.modulos.zonas.schemas import (
    ActualizarZonaRequest,
    CrearZonaRequest,
    ZonaResponse,
    ZonasPaginaResponse,
)
from app.modulos.zonas.service import ZonasService

router = APIRouter(
    prefix="/zonas",
    tags=["Zonas"],
    dependencies=[Depends(obtener_usuario_actual)],
)

Sesion = Annotated[AsyncSession, Depends(obtener_sesion)]


@router.get("", response_model=ZonasPaginaResponse, operation_id="listar_zonas")
async def listar_zonas(
    sesion: Sesion,
    q: str | None = Query(default=None),
    activo: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
) -> ZonasPaginaResponse:
    return await ZonasService(sesion).listar(
        q=q, activo=activo, page=page, page_size=page_size
    )


@router.get("/{zona_id}", response_model=ZonaResponse, operation_id="obtener_zona")
async def obtener_zona(zona_id: str, sesion: Sesion) -> ZonaResponse:
    return await ZonasService(sesion).obtener(zona_id)


@router.post(
    "",
    response_model=ZonaResponse,
    status_code=201,
    dependencies=[Depends(requerir_rol("administrador"))],
    operation_id="crear_zona",
)
async def crear_zona(datos: CrearZonaRequest, sesion: Sesion) -> ZonaResponse:
    return await ZonasService(sesion).crear(datos)


@router.put(
    "/{zona_id}",
    response_model=ZonaResponse,
    dependencies=[Depends(requerir_rol("administrador"))],
    operation_id="actualizar_zona",
)
async def actualizar_zona(
    zona_id: str, datos: ActualizarZonaRequest, sesion: Sesion
) -> ZonaResponse:
    return await ZonasService(sesion).actualizar(zona_id, datos)


@router.patch(
    "/{zona_id}/desactivar",
    response_model=ZonaResponse,
    dependencies=[Depends(requerir_rol("administrador"))],
    operation_id="desactivar_zona",
)
async def desactivar_zona(zona_id: str, sesion: Sesion) -> ZonaResponse:
    return await ZonasService(sesion).desactivar(zona_id)
