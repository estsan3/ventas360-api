"""Capa API del módulo ventas."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import obtener_sesion
from app.core.dependencias import obtener_usuario_actual
from app.modulos.ventas.schemas import (
    CambiarEstadoPedidoRequest,
    CrearPedidoRequest,
    PedidoResponse,
)
from app.modulos.ventas.service import VentasService

router = APIRouter(
    prefix="/ventas",
    tags=["Ventas"],
    dependencies=[Depends(obtener_usuario_actual)],
)

Sesion = Annotated[AsyncSession, Depends(obtener_sesion)]


@router.get("/pedidos", response_model=list[PedidoResponse], operation_id="listar_pedidos")
async def listar_pedidos(sesion: Sesion) -> list[PedidoResponse]:
    """Lista todos los pedidos."""
    return await VentasService(sesion).listar()


@router.get(
    "/pedidos/{pedido_id}",
    response_model=PedidoResponse,
    operation_id="obtener_pedido",
)
async def obtener_pedido(pedido_id: str, sesion: Sesion) -> PedidoResponse:
    """Obtiene un pedido por ID."""
    return await VentasService(sesion).obtener(pedido_id)


@router.post(
    "/pedidos",
    response_model=PedidoResponse,
    status_code=201,
    operation_id="crear_pedido",
)
async def crear_pedido(datos: CrearPedidoRequest, sesion: Sesion) -> PedidoResponse:
    """Crea un pedido con sus líneas."""
    return await VentasService(sesion).crear(datos)


@router.patch(
    "/pedidos/{pedido_id}/estado",
    response_model=PedidoResponse,
    operation_id="cambiar_estado_pedido",
)
async def cambiar_estado_pedido(
    pedido_id: str, datos: CambiarEstadoPedidoRequest, sesion: Sesion
) -> PedidoResponse:
    """Cambia el estado de un pedido."""
    return await VentasService(sesion).cambiar_estado(pedido_id, datos)
