"""API del módulo caja."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import obtener_sesion
from app.core.dependencias import UsuarioActual, obtener_usuario_actual
from app.modulos.caja.schemas import (
    AbrirCajaRequest,
    CerrarCajaRequest,
    CrearMovimientoCajaRequest,
    MovimientoCajaResponse,
    SaldoCajaResponse,
)
from app.modulos.caja.service import CajaService
from app.modulos.tenants.dependencias import exigir_usuario_del_comercio, requerir_modulo

router = APIRouter(
    prefix="/caja",
    tags=["Caja"],
    dependencies=[
        Depends(exigir_usuario_del_comercio),
        Depends(requerir_modulo("compras")),
    ],
)

Sesion = Annotated[AsyncSession, Depends(obtener_sesion)]
Usuario = Annotated[UsuarioActual, Depends(obtener_usuario_actual)]


@router.get(
    "/movimientos",
    response_model=list[MovimientoCajaResponse],
    operation_id="listar_movimientos_caja",
)
async def listar_movimientos(
    sesion: Sesion,
    fecha: date | None = Query(default=None),
) -> list[MovimientoCajaResponse]:
    return await CajaService(sesion).listar_movimientos(fecha)


@router.get("/saldo", response_model=SaldoCajaResponse, operation_id="saldo_caja")
async def saldo_caja(
    sesion: Sesion,
    fecha: date | None = Query(default=None),
) -> SaldoCajaResponse:
    return await CajaService(sesion).saldo(fecha)


@router.post(
    "/abrir",
    response_model=SaldoCajaResponse,
    operation_id="abrir_caja",
)
async def abrir_caja(
    datos: AbrirCajaRequest, sesion: Sesion, usuario: Usuario
) -> SaldoCajaResponse:
    return await CajaService(sesion).abrir(datos, usuario.email or usuario.id)


@router.post(
    "/cerrar",
    response_model=SaldoCajaResponse,
    operation_id="cerrar_caja",
)
async def cerrar_caja(
    datos: CerrarCajaRequest, sesion: Sesion, usuario: Usuario
) -> SaldoCajaResponse:
    return await CajaService(sesion).cerrar(datos, usuario.email or usuario.id)


@router.post(
    "/movimientos",
    response_model=MovimientoCajaResponse,
    status_code=201,
    operation_id="crear_movimiento_caja",
)
async def crear_movimiento(
    datos: CrearMovimientoCajaRequest, sesion: Sesion
) -> MovimientoCajaResponse:
    return await CajaService(sesion).crear_movimiento(datos)
