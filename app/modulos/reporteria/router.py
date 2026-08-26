"""Capa API del módulo reportería."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import obtener_sesion
from app.modulos.reporteria.schemas import KpisResponse
from app.modulos.reporteria.service import ReporteriaService
from app.modulos.tenants.dependencias import exigir_usuario_del_comercio, requerir_modulo

router = APIRouter(
    prefix="/reporteria",
    tags=["Reportería"],
    dependencies=[
        Depends(exigir_usuario_del_comercio),
        Depends(requerir_modulo("inicio")),
    ],
)

Sesion = Annotated[AsyncSession, Depends(obtener_sesion)]


@router.get("/kpis", response_model=KpisResponse, operation_id="obtener_kpis")
async def obtener_kpis(sesion: Sesion) -> KpisResponse:
    """KPIs del dashboard: clientes, productos, ventas del mes y ticket promedio."""
    return await ReporteriaService(sesion).obtener_kpis()
