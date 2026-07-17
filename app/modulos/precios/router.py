"""API del módulo precios."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import obtener_sesion
from app.core.dependencias import obtener_usuario_actual, requerir_rol
from app.modulos.precios.schemas import (
    CrearListaPrecioRequest,
    ListaPrecioResponse,
    PrecioArticuloResponse,
    PrecioResueltoResponse,
    UpsertPrecioArticuloRequest,
)
from app.modulos.precios.service import PreciosService

router = APIRouter(
    prefix="/precios",
    tags=["Precios"],
    dependencies=[Depends(obtener_usuario_actual)],
)

Sesion = Annotated[AsyncSession, Depends(obtener_sesion)]


@router.get(
    "/listas",
    response_model=list[ListaPrecioResponse],
    operation_id="listar_listas_precio",
)
async def listar_listas(sesion: Sesion) -> list[ListaPrecioResponse]:
    return await PreciosService(sesion).listar_listas()


@router.post(
    "/listas",
    response_model=ListaPrecioResponse,
    status_code=201,
    dependencies=[Depends(requerir_rol("administrador"))],
    operation_id="crear_lista_precio",
)
async def crear_lista(
    datos: CrearListaPrecioRequest, sesion: Sesion
) -> ListaPrecioResponse:
    return await PreciosService(sesion).crear_lista(datos)


@router.put(
    "/articulos",
    response_model=PrecioArticuloResponse,
    dependencies=[Depends(requerir_rol("administrador"))],
    operation_id="upsert_precio_articulo",
)
async def upsert_precio(
    datos: UpsertPrecioArticuloRequest, sesion: Sesion
) -> PrecioArticuloResponse:
    return await PreciosService(sesion).upsert_precio(datos)


@router.get(
    "/resolver",
    response_model=PrecioResueltoResponse,
    operation_id="resolver_precio",
)
async def resolver_precio(
    sesion: Sesion,
    articulo_id: str = Query(...),
    cliente_id: str | None = Query(default=None),
) -> PrecioResueltoResponse:
    return await PreciosService(sesion).resolver_precio(articulo_id, cliente_id)
