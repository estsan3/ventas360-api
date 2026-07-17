"""Capa API del módulo ventas."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
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
async def listar_pedidos(
    sesion: Sesion,
    tipo: Literal["pedido", "remito", "factura"] | None = Query(default=None),
) -> list[PedidoResponse]:
    """Lista comprobantes (opcionalmente filtrados por tipo)."""
    return await VentasService(sesion).listar(tipo=tipo)


@router.get(
    "/pedidos/{pedido_id}",
    response_model=PedidoResponse,
    operation_id="obtener_pedido",
)
async def obtener_pedido(pedido_id: str, sesion: Sesion) -> PedidoResponse:
    """Obtiene un comprobante por ID."""
    return await VentasService(sesion).obtener(pedido_id)


@router.post(
    "/pedidos",
    response_model=PedidoResponse,
    status_code=201,
    operation_id="crear_pedido",
)
async def crear_pedido(datos: CrearPedidoRequest, sesion: Sesion) -> PedidoResponse:
    """Crea un comprobante tipado (pedido, remito o factura) con sus líneas."""
    return await VentasService(sesion).crear(datos)


@router.patch(
    "/pedidos/{pedido_id}/estado",
    response_model=PedidoResponse,
    operation_id="cambiar_estado_pedido",
)
async def cambiar_estado_pedido(
    pedido_id: str, datos: CambiarEstadoPedidoRequest, sesion: Sesion
) -> PedidoResponse:
    """Cambia el estado. Confirmar remito descuenta stock."""
    return await VentasService(sesion).cambiar_estado(pedido_id, datos)


@router.post(
    "/pedidos/{pedido_id}/confirmar-remito",
    response_model=PedidoResponse,
    operation_id="confirmar_remito",
)
async def confirmar_remito(pedido_id: str, sesion: Sesion) -> PedidoResponse:
    """Confirma un remito en borrador y egresa stock del depósito."""
    return await VentasService(sesion).confirmar_remito(pedido_id)


@router.post(
    "/pedidos/{pedido_id}/facturar",
    response_model=PedidoResponse,
    operation_id="facturar_remito",
)
async def facturar_remito(pedido_id: str, sesion: Sesion) -> PedidoResponse:
    """Convierte un remito confirmado en factura."""
    return await VentasService(sesion).convertir_remito_a_factura(pedido_id)
