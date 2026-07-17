"""API del módulo cxc."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import obtener_sesion
from app.core.dependencias import obtener_usuario_actual, requerir_rol
from app.modulos.cxc.schemas import (
    EstadoCuentaResponse,
    MovimientoCxcResponse,
    RegistrarMovimientoRequest,
    SaldoClienteResponse,
)
from app.modulos.cxc.service import CxcService

router = APIRouter(
    prefix="/cxc",
    tags=["Cuenta corriente"],
    dependencies=[Depends(obtener_usuario_actual)],
)

Sesion = Annotated[AsyncSession, Depends(obtener_sesion)]


@router.get(
    "/saldos",
    response_model=list[SaldoClienteResponse],
    operation_id="listar_saldos_cxc",
)
async def listar_saldos(sesion: Sesion) -> list[SaldoClienteResponse]:
    return await CxcService(sesion).listar_saldos()


@router.get(
    "/clientes/{cliente_id}/saldo",
    response_model=SaldoClienteResponse,
    operation_id="obtener_saldo_cxc",
)
async def obtener_saldo(cliente_id: str, sesion: Sesion) -> SaldoClienteResponse:
    return await CxcService(sesion).saldo(cliente_id)


@router.get(
    "/clientes/{cliente_id}/estado-cuenta",
    response_model=EstadoCuentaResponse,
    operation_id="estado_cuenta_cxc",
)
async def estado_cuenta(cliente_id: str, sesion: Sesion) -> EstadoCuentaResponse:
    return await CxcService(sesion).estado_cuenta(cliente_id)


@router.post(
    "/ajustes",
    response_model=MovimientoCxcResponse,
    status_code=201,
    dependencies=[Depends(requerir_rol("administrador"))],
    operation_id="registrar_ajuste_cxc",
)
async def registrar_ajuste(
    datos: RegistrarMovimientoRequest, sesion: Sesion
) -> MovimientoCxcResponse:
    return await CxcService(sesion).registrar_ajuste(datos)
