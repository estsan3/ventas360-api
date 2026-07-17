"""API del módulo caja."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import obtener_sesion
from app.core.dependencias import obtener_usuario_actual, requerir_rol
from app.modulos.caja.schemas import (
    CrearMovimientoCajaRequest,
    MovimientoCajaResponse,
    SaldoCajaResponse,
)
from app.modulos.caja.service import CajaService

router = APIRouter(
    prefix="/caja",
    tags=["Caja"],
    dependencies=[Depends(obtener_usuario_actual)],
)

Sesion = Annotated[AsyncSession, Depends(obtener_sesion)]


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
    "/movimientos",
    response_model=MovimientoCajaResponse,
    status_code=201,
    dependencies=[Depends(requerir_rol("administrador"))],
    operation_id="crear_movimiento_caja",
)
async def crear_movimiento(
    datos: CrearMovimientoCajaRequest, sesion: Sesion
) -> MovimientoCajaResponse:
    return await CajaService(sesion).crear_movimiento(datos)
