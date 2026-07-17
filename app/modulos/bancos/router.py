"""API del módulo bancos."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import obtener_sesion
from app.core.dependencias import obtener_usuario_actual, requerir_rol
from app.modulos.bancos.schemas import (
    CrearCuentaBancariaRequest,
    CrearValorRequest,
    CuentaBancariaResponse,
    DepositarValorRequest,
    MovimientoBancarioResponse,
    ValorBancarioResponse,
)
from app.modulos.bancos.service import BancosService

router = APIRouter(
    prefix="/bancos",
    tags=["Bancos"],
    dependencies=[Depends(obtener_usuario_actual)],
)

Sesion = Annotated[AsyncSession, Depends(obtener_sesion)]


@router.get(
    "/cuentas",
    response_model=list[CuentaBancariaResponse],
    operation_id="listar_cuentas_bancarias",
)
async def listar_cuentas(sesion: Sesion) -> list[CuentaBancariaResponse]:
    return await BancosService(sesion).listar_cuentas()


@router.post(
    "/cuentas",
    response_model=CuentaBancariaResponse,
    status_code=201,
    dependencies=[Depends(requerir_rol("administrador"))],
    operation_id="crear_cuenta_bancaria",
)
async def crear_cuenta(
    datos: CrearCuentaBancariaRequest, sesion: Sesion
) -> CuentaBancariaResponse:
    return await BancosService(sesion).crear_cuenta(datos)


@router.get(
    "/movimientos",
    response_model=list[MovimientoBancarioResponse],
    operation_id="listar_movimientos_bancarios",
)
async def listar_movimientos(
    sesion: Sesion,
    cuenta_id: str | None = Query(default=None),
) -> list[MovimientoBancarioResponse]:
    return await BancosService(sesion).listar_movimientos(cuenta_id)


@router.get(
    "/valores",
    response_model=list[ValorBancarioResponse],
    operation_id="listar_valores_bancarios",
)
async def listar_valores(
    sesion: Sesion,
    estado: str | None = Query(default=None),
) -> list[ValorBancarioResponse]:
    return await BancosService(sesion).listar_valores(estado)


@router.post(
    "/valores",
    response_model=ValorBancarioResponse,
    status_code=201,
    dependencies=[Depends(requerir_rol("administrador"))],
    operation_id="crear_valor_bancario",
)
async def crear_valor(
    datos: CrearValorRequest, sesion: Sesion
) -> ValorBancarioResponse:
    return await BancosService(sesion).crear_valor(datos)


@router.post(
    "/valores/{valor_id}/depositar",
    response_model=ValorBancarioResponse,
    dependencies=[Depends(requerir_rol("administrador"))],
    operation_id="depositar_valor_bancario",
)
async def depositar_valor(
    valor_id: str, datos: DepositarValorRequest, sesion: Sesion
) -> ValorBancarioResponse:
    return await BancosService(sesion).depositar_valor(valor_id, datos)
