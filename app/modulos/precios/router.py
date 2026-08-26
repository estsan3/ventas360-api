"""API del módulo precios."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import obtener_sesion
from app.modulos.precios.schemas import (
    ActualizarListaPrecioRequest,
    CrearListaPrecioRequest,
    ListaPrecioResponse,
    PrecioArticuloResponse,
    PrecioResueltoResponse,
    UpsertPrecioArticuloRequest,
)
from app.modulos.precios.service import PreciosService
from app.modulos.tenants.dependencias import exigir_usuario_del_comercio, requerir_modulo

router = APIRouter(
    prefix="/precios",
    tags=["Precios"],
    dependencies=[Depends(exigir_usuario_del_comercio)],
)

Sesion = Annotated[AsyncSession, Depends(obtener_sesion)]


@router.get(
    "/listas",
    response_model=list[ListaPrecioResponse],
    dependencies=[Depends(requerir_modulo("articulos", "cta_cte", "mostrador", "compras"))],
    operation_id="listar_listas_precio",
)
async def listar_listas(sesion: Sesion) -> list[ListaPrecioResponse]:
    return await PreciosService(sesion).listar_listas()


@router.post(
    "/listas",
    response_model=ListaPrecioResponse,
    status_code=201,
    dependencies=[Depends(requerir_modulo("articulos"))],
    operation_id="crear_lista_precio",
)
async def crear_lista(
    datos: CrearListaPrecioRequest, sesion: Sesion
) -> ListaPrecioResponse:
    return await PreciosService(sesion).crear_lista(datos)


@router.put(
    "/listas/{lista_id}",
    response_model=ListaPrecioResponse,
    dependencies=[Depends(requerir_modulo("articulos"))],
    operation_id="actualizar_lista_precio",
)
async def actualizar_lista(
    lista_id: str, datos: ActualizarListaPrecioRequest, sesion: Sesion
) -> ListaPrecioResponse:
    return await PreciosService(sesion).actualizar_lista(lista_id, datos)


@router.patch(
    "/listas/{lista_id}/desactivar",
    response_model=ListaPrecioResponse,
    dependencies=[Depends(requerir_modulo("articulos"))],
    operation_id="desactivar_lista_precio",
)
async def desactivar_lista(lista_id: str, sesion: Sesion) -> ListaPrecioResponse:
    return await PreciosService(sesion).desactivar_lista(lista_id)


@router.get(
    "/listas/{lista_id}/articulos",
    response_model=list[PrecioArticuloResponse],
    dependencies=[Depends(requerir_modulo("articulos", "cta_cte", "mostrador", "compras"))],
    operation_id="listar_precios_lista",
)
async def listar_precios_lista(
    lista_id: str, sesion: Sesion
) -> list[PrecioArticuloResponse]:
    return await PreciosService(sesion).listar_precios_lista(lista_id)


@router.put(
    "/articulos",
    response_model=PrecioArticuloResponse,
    dependencies=[Depends(requerir_modulo("articulos"))],
    operation_id="upsert_precio_articulo",
)
async def upsert_precio(
    datos: UpsertPrecioArticuloRequest, sesion: Sesion
) -> PrecioArticuloResponse:
    return await PreciosService(sesion).upsert_precio(datos)


@router.get(
    "/resolver",
    response_model=PrecioResueltoResponse,
    dependencies=[Depends(requerir_modulo("articulos", "cta_cte", "mostrador", "compras"))],
    operation_id="resolver_precio",
)
async def resolver_precio(
    sesion: Sesion,
    articulo_id: str = Query(...),
    cliente_id: str | None = Query(default=None),
) -> PrecioResueltoResponse:
    return await PreciosService(sesion).resolver_precio(articulo_id, cliente_id)
