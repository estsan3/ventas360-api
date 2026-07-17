"""API del módulo compras."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import obtener_sesion
from app.core.dependencias import obtener_usuario_actual, requerir_rol
from app.modulos.compras.schemas import CompraResponse, CrearCompraRequest
from app.modulos.compras.service import ComprasService

router = APIRouter(
    prefix="/compras",
    tags=["Compras"],
    dependencies=[Depends(obtener_usuario_actual)],
)

Sesion = Annotated[AsyncSession, Depends(obtener_sesion)]


@router.get("", response_model=list[CompraResponse], operation_id="listar_compras")
async def listar_compras(
    sesion: Sesion,
    tipo: str | None = Query(default=None),
) -> list[CompraResponse]:
    return await ComprasService(sesion).listar(tipo=tipo)


@router.get("/{compra_id}", response_model=CompraResponse, operation_id="obtener_compra")
async def obtener_compra(compra_id: str, sesion: Sesion) -> CompraResponse:
    return await ComprasService(sesion).obtener(compra_id)


@router.post(
    "",
    response_model=CompraResponse,
    status_code=201,
    dependencies=[Depends(requerir_rol("administrador"))],
    operation_id="crear_compra",
)
async def crear_compra(datos: CrearCompraRequest, sesion: Sesion) -> CompraResponse:
    return await ComprasService(sesion).crear(datos)


@router.post(
    "/{compra_id}/confirmar",
    response_model=CompraResponse,
    dependencies=[Depends(requerir_rol("administrador"))],
    operation_id="confirmar_compra",
)
async def confirmar_compra(compra_id: str, sesion: Sesion) -> CompraResponse:
    return await ComprasService(sesion).confirmar(compra_id)


@router.post(
    "/{compra_id}/facturar",
    response_model=CompraResponse,
    dependencies=[Depends(requerir_rol("administrador"))],
    operation_id="facturar_remito_compra",
)
async def facturar_remito_compra(compra_id: str, sesion: Sesion) -> CompraResponse:
    return await ComprasService(sesion).facturar_remito(compra_id)
