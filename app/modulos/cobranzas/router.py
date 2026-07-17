"""API del módulo cobranzas."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import obtener_sesion
from app.core.dependencias import obtener_usuario_actual
from app.modulos.cobranzas.schemas import CrearReciboRequest, ReciboResponse
from app.modulos.cobranzas.service import CobranzasService

router = APIRouter(
    prefix="/cobranzas",
    tags=["Cobranzas"],
    dependencies=[Depends(obtener_usuario_actual)],
)

Sesion = Annotated[AsyncSession, Depends(obtener_sesion)]


@router.get(
    "/recibos",
    response_model=list[ReciboResponse],
    operation_id="listar_recibos",
)
async def listar_recibos(
    sesion: Sesion,
    cliente_id: str | None = Query(default=None),
) -> list[ReciboResponse]:
    return await CobranzasService(sesion).listar(cliente_id=cliente_id)


@router.get(
    "/recibos/{recibo_id}",
    response_model=ReciboResponse,
    operation_id="obtener_recibo",
)
async def obtener_recibo(recibo_id: str, sesion: Sesion) -> ReciboResponse:
    return await CobranzasService(sesion).obtener(recibo_id)


@router.post(
    "/recibos",
    response_model=ReciboResponse,
    status_code=201,
    operation_id="crear_recibo",
)
async def crear_recibo(datos: CrearReciboRequest, sesion: Sesion) -> ReciboResponse:
    return await CobranzasService(sesion).crear(datos)
