"""DTOs del módulo stock."""

from datetime import datetime

from pydantic import BaseModel, Field


class DepositoResponse(BaseModel):
    id: str
    codigo: str
    nombre: str
    activo: bool

    model_config = {"from_attributes": True}


class CrearDepositoRequest(BaseModel):
    codigo: str = Field(min_length=1, max_length=20)
    nombre: str = Field(min_length=1, max_length=120)


class ActualizarDepositoRequest(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=120)


class SaldoResponse(BaseModel):
    id: str
    articulo_id: str
    deposito_id: str
    cantidad: int

    model_config = {"from_attributes": True}


class InventarioItemResponse(BaseModel):
    """Fila de inventario de un depósito (catálogo + saldo real)."""

    articulo_id: str
    sku: str
    nombre: str
    deposito_id: str
    cantidad: int
    costo: float
    precio: float
    marca: str = ""
    rubro: str = ""
    codigo_barras: str = ""


class AjusteStockRequest(BaseModel):
    articulo_id: str = Field(min_length=1, max_length=36)
    deposito_id: str = Field(min_length=1, max_length=36)
    cantidad: int  # delta (+/-)
    referencia: str = Field(default="", max_length=80)


class ConteoTomaItemRequest(BaseModel):
    articulo_id: str = Field(min_length=1, max_length=36)
    cantidad: int = Field(ge=0)


class CerrarTomaRequest(BaseModel):
    deposito_id: str = Field(min_length=1, max_length=36)
    conteos: list[ConteoTomaItemRequest] = Field(min_length=1, max_length=2000)


class AjusteTomaItemResponse(BaseModel):
    articulo_id: str
    sku: str
    anterior: int
    nuevo: int
    delta: int


class CerrarTomaResponse(BaseModel):
    deposito_id: str
    ajustados: int
    sin_cambio: int
    ajustes: list[AjusteTomaItemResponse]


class MovimientoResponse(BaseModel):
    id: str
    articulo_id: str
    deposito_id: str
    tipo: str
    cantidad: int
    referencia: str
    creado_en: datetime | None = None

    model_config = {"from_attributes": True}
