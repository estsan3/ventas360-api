"""API CxP."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import obtener_sesion
from app.modulos.cxp.schemas import EstadoCuentaProveedorResponse, SaldoProveedorResponse
from app.modulos.cxp.service import CxpService
from app.modulos.tenants.dependencias import exigir_usuario_del_comercio, requerir_modulo

router = APIRouter(
    prefix="/cxp",
    tags=["Cuenta corriente proveedores"],
    dependencies=[
        Depends(exigir_usuario_del_comercio),
        Depends(requerir_modulo("compras")),
    ],
)

Sesion = Annotated[AsyncSession, Depends(obtener_sesion)]


@router.get("/saldos", response_model=list[SaldoProveedorResponse], operation_id="listar_saldos_cxp")
async def listar_saldos(sesion: Sesion) -> list[SaldoProveedorResponse]:
    return await CxpService(sesion).listar_saldos()


@router.get(
    "/proveedores/{proveedor_id}",
    response_model=EstadoCuentaProveedorResponse,
    operation_id="estado_cuenta_proveedor",
)
async def estado_cuenta(
    proveedor_id: str, sesion: Sesion
) -> EstadoCuentaProveedorResponse:
    return await CxpService(sesion).estado_cuenta(proveedor_id)
