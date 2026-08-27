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


class LineaRemitoParseadaResponse(BaseModel):
    descripcion_extraida: str
    sku_extraido: str | None = None
    codigo_barras_extraido: str | None = None
    cantidad: int
    precio_unitario: float | None = None
    producto_id: str | None = None
    producto_nombre: str | None = None
    producto_sku: str | None = None
    match_tipo: str | None = None
    confianza: str


class ParsearRemitoResponse(BaseModel):
    numero_remito: str | None = None
    fecha: str | None = None
    proveedor_texto: str | None = None
    proveedor_id: str | None = None
    deposito_id: str | None = None
    lineas: list[LineaRemitoParseadaResponse]
    sin_match: int
    advertencias: list[str] = Field(default_factory=list)
    confianza_extraccion: float
    modo_parser: str
