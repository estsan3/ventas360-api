"""Capa API del módulo parámetros."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import obtener_sesion
from app.modulos.parametros.schemas import (
    ParametrosAfip,
    ParametrosAfipResponse,
    ParametrosNegocio,
    ParametrosOperativos,
    PreferenciasNotificacion,
    TalonarioResponse,
    UpsertTalonarioRequest,
)
from app.modulos.parametros.service import ParametrosService
from app.modulos.tenants.dependencias import exigir_usuario_del_comercio, requerir_modulo

router = APIRouter(
    tags=["Parámetros"],
    dependencies=[Depends(exigir_usuario_del_comercio)],
)

Sesion = Annotated[AsyncSession, Depends(obtener_sesion)]


@router.get(
    "/parametros",
    response_model=ParametrosNegocio,
    dependencies=[Depends(requerir_modulo("mostrador", "ventas", "configuracion", "inicio"))],
    operation_id="obtener_parametros",
)
async def obtener_negocio(sesion: Sesion) -> ParametrosNegocio:
    return await ParametrosService(sesion).obtener_negocio()


@router.put(
    "/parametros",
    response_model=ParametrosNegocio,
    dependencies=[Depends(requerir_modulo("configuracion"))],
    operation_id="guardar_parametros",
)
async def guardar_negocio(datos: ParametrosNegocio, sesion: Sesion) -> ParametrosNegocio:
    return await ParametrosService(sesion).guardar_negocio(datos)


@router.get(
    "/parametros/afip",
    response_model=ParametrosAfipResponse,
    dependencies=[Depends(requerir_modulo("mostrador", "ventas", "configuracion"))],
    operation_id="obtener_parametros_afip",
)
async def obtener_afip(sesion: Sesion) -> ParametrosAfipResponse:
    return await ParametrosService(sesion).obtener_afip()


@router.put(
    "/parametros/afip",
    response_model=ParametrosAfipResponse,
    dependencies=[Depends(requerir_modulo("configuracion"))],
    operation_id="guardar_parametros_afip",
)
async def guardar_afip(datos: ParametrosAfip, sesion: Sesion) -> ParametrosAfipResponse:
    return await ParametrosService(sesion).guardar_afip(datos)


@router.get(
    "/parametros/operativos",
    response_model=ParametrosOperativos,
    dependencies=[Depends(requerir_modulo("configuracion"))],
    operation_id="obtener_parametros_operativos",
)
async def obtener_operativos(sesion: Sesion) -> ParametrosOperativos:
    return await ParametrosService(sesion).obtener_operativos()


@router.put(
    "/parametros/operativos",
    response_model=ParametrosOperativos,
    dependencies=[Depends(requerir_modulo("configuracion"))],
    operation_id="guardar_parametros_operativos",
)
async def guardar_operativos(
    datos: ParametrosOperativos, sesion: Sesion
) -> ParametrosOperativos:
    return await ParametrosService(sesion).guardar_operativos(datos)


@router.get(
    "/parametros/talonarios",
    response_model=list[TalonarioResponse],
    dependencies=[Depends(requerir_modulo("ventas", "mostrador", "configuracion"))],
    operation_id="listar_talonarios",
)
async def listar_talonarios(sesion: Sesion) -> list[TalonarioResponse]:
    return await ParametrosService(sesion).listar_talonarios()


@router.put(
    "/parametros/talonarios",
    response_model=TalonarioResponse,
    dependencies=[Depends(requerir_modulo("configuracion"))],
    operation_id="upsert_talonario",
)
async def upsert_talonario(
    datos: UpsertTalonarioRequest, sesion: Sesion
) -> TalonarioResponse:
    return await ParametrosService(sesion).upsert_talonario(datos)


@router.get(
    "/preferencias",
    response_model=PreferenciasNotificacion,
    operation_id="obtener_preferencias",
)
async def obtener_preferencias(sesion: Sesion) -> PreferenciasNotificacion:
    return await ParametrosService(sesion).obtener_preferencias()


@router.put(
    "/preferencias",
    response_model=PreferenciasNotificacion,
    operation_id="guardar_preferencias",
)
async def guardar_preferencias(
    datos: PreferenciasNotificacion, sesion: Sesion
) -> PreferenciasNotificacion:
    return await ParametrosService(sesion).guardar_preferencias(datos)


@router.get(
    "/parametria/categorias-producto",
    response_model=list[str],
    dependencies=[Depends(requerir_modulo("articulos", "mostrador"))],
    operation_id="listar_categorias_producto",
)
async def listar_categorias_producto() -> list[str]:
    return ["Electrónica", "Hogar", "Indumentaria", "Alimentos", "Otros"]
