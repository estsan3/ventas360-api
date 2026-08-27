"""API del módulo IA."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import obtener_sesion
from app.modulos.ia.dependencias import fijar_tenant_por_slug, verificar_webhook_n8n
from app.modulos.ia.schemas import (
    AccionesDiaResponse,
    InterpretarMostradorRequest,
    InterpretarMostradorResponse,
    ResumenDiaResponse,
)
from app.modulos.ia.service import IaService
from app.modulos.tenants.dependencias import exigir_usuario_del_comercio, requerir_modulo

router = APIRouter(prefix="/ai", tags=["IA"])

Sesion = Annotated[AsyncSession, Depends(obtener_sesion)]


@router.post(
    "/mostrador/interpretar",
    response_model=InterpretarMostradorResponse,
    operation_id="interpretar_mostrador",
    dependencies=[
        Depends(exigir_usuario_del_comercio),
        Depends(requerir_modulo("mostrador")),
    ],
)
async def interpretar_mostrador(
    datos: InterpretarMostradorRequest, sesion: Sesion
) -> InterpretarMostradorResponse:
    return await IaService(sesion).interpretar_mostrador(datos)


@router.get(
    "/acciones",
    response_model=AccionesDiaResponse,
    operation_id="acciones_del_dia",
    dependencies=[
        Depends(exigir_usuario_del_comercio),
        Depends(requerir_modulo("inicio")),
    ],
)
async def acciones_del_dia(sesion: Sesion) -> AccionesDiaResponse:
    return await IaService(sesion).acciones_del_dia()


@router.get(
    "/resumen-dia",
    response_model=ResumenDiaResponse,
    operation_id="resumen_dia",
    dependencies=[
        Depends(exigir_usuario_del_comercio),
        Depends(requerir_modulo("inicio")),
    ],
)
async def resumen_dia(
    sesion: Sesion,
    narrativa: bool = Query(default=True),
) -> ResumenDiaResponse:
    return await IaService(sesion).resumen_dia(narrativa=narrativa)


@router.get(
    "/webhook/resumen-dia",
    response_model=ResumenDiaResponse,
    operation_id="webhook_resumen_dia_n8n",
    dependencies=[
        Depends(verificar_webhook_n8n),
        Depends(fijar_tenant_por_slug),
    ],
)
async def webhook_resumen_dia_n8n(
    sesion: Sesion,
    narrativa: bool = Query(default=True),
) -> ResumenDiaResponse:
    """Endpoint para n8n / automatizaciones (sin JWT, con secreto + tenant slug)."""
    return await IaService(sesion).resumen_dia(narrativa=narrativa)
