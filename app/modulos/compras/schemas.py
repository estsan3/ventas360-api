"""DTOs del módulo compras."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

TipoCompra = Literal["remito_compra", "factura_compra"]


class LineaCompraResponse(BaseModel):
    id: str
    producto_id: str
    descripcion: str = ""
    cantidad: int
    precio_unitario: float

    model_config = {"from_attributes": True}


class CompraResponse(BaseModel):
    id: str
    tipo: TipoCompra
    proveedor_id: str
    estado: str
    deposito_id: str | None = None
    origen_id: str | None = None
    neto: float
    iva: float
    iva_porcentaje: float
    total: float
    numero: str | None = None
    fecha: date
    lineas: list[LineaCompraResponse]

    model_config = {"from_attributes": True}


class CrearLineaCompraRequest(BaseModel):
    producto_id: str
    cantidad: int = Field(gt=0)
    precio_unitario: float | None = Field(default=None, ge=0)


class CrearCompraRequest(BaseModel):
    proveedor_id: str
    tipo: TipoCompra = "remito_compra"
    deposito_id: str
    fecha: date | None = None
    lineas: list[CrearLineaCompraRequest] = Field(min_length=1)
