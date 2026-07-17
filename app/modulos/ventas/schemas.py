"""DTOs del módulo ventas."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class LineaPedidoResponse(BaseModel):
    """Línea de pedido expuesta por la API."""

    id: str
    producto_id: str
    cantidad: int
    precio_unitario: float

    model_config = {"from_attributes": True}


class PedidoResponse(BaseModel):
    """Pedido expuesto por la API."""

    id: str
    cliente_id: str
    estado: str
    total: float
    fecha: date
    lineas: list[LineaPedidoResponse]

    model_config = {"from_attributes": True}


class CrearLineaPedidoRequest(BaseModel):
    """Línea al crear un pedido."""

    producto_id: str
    cantidad: int = Field(gt=0)


class CrearPedidoRequest(BaseModel):
    """Alta de pedido con sus líneas."""

    cliente_id: str
    fecha: date | None = None
    lineas: list[CrearLineaPedidoRequest] = Field(min_length=1)


class CambiarEstadoPedidoRequest(BaseModel):
    """Cambio de estado de un pedido."""

    estado: Literal["borrador", "confirmado", "entregado", "cancelado"]
