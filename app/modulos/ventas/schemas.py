"""DTOs del módulo ventas (comprobantes tipados)."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

TipoComprobante = Literal["pedido", "remito", "factura"]
EstadoComprobante = Literal[
    "borrador",
    "confirmado",
    "entregado",
    "facturado",
    "cancelado",
]


class LineaPedidoResponse(BaseModel):
    """Línea de comprobante."""

    id: str
    producto_id: str
    descripcion: str = ""
    cantidad: int
    precio_unitario: float

    model_config = {"from_attributes": True}


class PedidoResponse(BaseModel):
    """Comprobante expuesto por la API (nombre histórico: pedido)."""

    id: str
    tipo: TipoComprobante
    cliente_id: str
    estado: str
    deposito_id: str | None = None
    origen_id: str | None = None
    neto: float
    iva: float
    iva_porcentaje: float
    total: float
    cae: str | None = None
    numero: str | None = None
    fecha: date
    lineas: list[LineaPedidoResponse]

    model_config = {"from_attributes": True}


class CrearLineaPedidoRequest(BaseModel):
    """Línea al crear un comprobante."""

    producto_id: str
    cantidad: int = Field(gt=0)


class CrearPedidoRequest(BaseModel):
    """Alta de comprobante tipado con sus líneas."""

    cliente_id: str
    tipo: TipoComprobante = "pedido"
    deposito_id: str | None = None
    fecha: date | None = None
    lineas: list[CrearLineaPedidoRequest] = Field(min_length=1)


class CambiarEstadoPedidoRequest(BaseModel):
    """Cambio de estado genérico (pedidos / facturas en borrador)."""

    estado: EstadoComprobante
