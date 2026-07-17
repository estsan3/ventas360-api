"""API del módulo stock."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import obtener_sesion
from app.core.dependencias import obtener_usuario_actual, requerir_rol
from app.modulos.stock.schemas import (
    ActualizarDepositoRequest,
    AjusteStockRequest,
    CrearDepositoRequest,
    DepositoResponse,
    InventarioItemResponse,
    SaldoResponse,
)
from app.modulos.stock.service import StockService

router = APIRouter(
    prefix="/stock",
    tags=["Stock"],
    dependencies=[Depends(obtener_usuario_actual)],
)

Sesion = Annotated[AsyncSession, Depends(obtener_sesion)]


@router.get(
    "/depositos",
    response_model=list[DepositoResponse],
    operation_id="listar_depositos",
)
async def listar_depositos(sesion: Sesion) -> list[DepositoResponse]:
    return await StockService(sesion).listar_depositos()


@router.post(
    "/depositos",
    response_model=DepositoResponse,
    status_code=201,
    dependencies=[Depends(requerir_rol("administrador"))],
    operation_id="crear_deposito",
)
async def crear_deposito(
    datos: CrearDepositoRequest, sesion: Sesion
) -> DepositoResponse:
    return await StockService(sesion).crear_deposito(datos)


@router.put(
    "/depositos/{deposito_id}",
    response_model=DepositoResponse,
    dependencies=[Depends(requerir_rol("administrador"))],
    operation_id="actualizar_deposito",
)
async def actualizar_deposito(
    deposito_id: str, datos: ActualizarDepositoRequest, sesion: Sesion
) -> DepositoResponse:
    return await StockService(sesion).actualizar_deposito(deposito_id, datos)


@router.patch(
    "/depositos/{deposito_id}/desactivar",
    response_model=DepositoResponse,
    dependencies=[Depends(requerir_rol("administrador"))],
    operation_id="desactivar_deposito",
)
async def desactivar_deposito(deposito_id: str, sesion: Sesion) -> DepositoResponse:
    return await StockService(sesion).desactivar_deposito(deposito_id)


@router.get(
    "/articulos/{articulo_id}/saldos",
    response_model=list[SaldoResponse],
    operation_id="listar_saldos_articulo",
)
async def listar_saldos_articulo(
    articulo_id: str, sesion: Sesion
) -> list[SaldoResponse]:
    return await StockService(sesion).listar_saldos_articulo(articulo_id)


@router.get(
    "/depositos/{deposito_id}/inventario",
    response_model=list[InventarioItemResponse],
    operation_id="listar_inventario_deposito",
)
async def listar_inventario_deposito(
    deposito_id: str, sesion: Sesion
) -> list[InventarioItemResponse]:
    return await StockService(sesion).listar_inventario_deposito(deposito_id)


@router.post(
    "/ajustes",
    response_model=SaldoResponse,
    dependencies=[Depends(requerir_rol("administrador"))],
    operation_id="ajustar_stock",
)
async def ajustar_stock(datos: AjusteStockRequest, sesion: Sesion) -> SaldoResponse:
    return await StockService(sesion).ajustar(datos)
