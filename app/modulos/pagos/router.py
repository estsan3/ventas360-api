"""API del módulo pagos a proveedores."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import obtener_sesion
from app.modulos.pagos.schemas import CrearPagoRequest, PagoResponse
from app.modulos.pagos.service import PagosService
from app.modulos.tenants.dependencias import exigir_usuario_del_comercio, requerir_modulo

router = APIRouter(
    prefix="/pagos",
    tags=["Pagos"],
    dependencies=[
        Depends(exigir_usuario_del_comercio),
        Depends(requerir_modulo("compras")),
    ],
)

Sesion = Annotated[AsyncSession, Depends(obtener_sesion)]


@router.get("", response_model=list[PagoResponse], operation_id="listar_pagos_proveedor")
async def listar_pagos(
    sesion: Sesion,
    proveedor_id: str | None = Query(default=None),
) -> list[PagoResponse]:
    return await PagosService(sesion).listar(proveedor_id=proveedor_id)


@router.get("/{pago_id}", response_model=PagoResponse, operation_id="obtener_pago_proveedor")
async def obtener_pago(pago_id: str, sesion: Sesion) -> PagoResponse:
    return await PagosService(sesion).obtener(pago_id)


@router.post(
    "",
    response_model=PagoResponse,
    status_code=201,
    operation_id="crear_pago_proveedor",
)
async def crear_pago(datos: CrearPagoRequest, sesion: Sesion) -> PagoResponse:
    return await PagosService(sesion).crear(datos)
