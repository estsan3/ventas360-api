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


class SaldoResponse(BaseModel):
    id: str
    articulo_id: str
    deposito_id: str
    cantidad: int

    model_config = {"from_attributes": True}


class AjusteStockRequest(BaseModel):
    articulo_id: str = Field(min_length=1, max_length=36)
    deposito_id: str = Field(min_length=1, max_length=36)
    cantidad: int  # delta (+/-)
    referencia: str = Field(default="", max_length=80)


class MovimientoResponse(BaseModel):
    id: str
    articulo_id: str
    deposito_id: str
    tipo: str
    cantidad: int
    referencia: str
    creado_en: datetime | None = None

    model_config = {"from_attributes": True}
