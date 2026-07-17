"""DTOs del módulo cobranzas."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

MedioCobro = Literal["efectivo", "transferencia", "tarjeta"]


class ImputacionResponse(BaseModel):
    id: str
    factura_id: str
    monto: float

    model_config = {"from_attributes": True}


class ReciboResponse(BaseModel):
    id: str
    cliente_id: str
    fecha: date
    monto: float
    medio: MedioCobro
    observacion: str
    imputaciones: list[ImputacionResponse]

    model_config = {"from_attributes": True}


class CrearImputacionRequest(BaseModel):
    factura_id: str = Field(min_length=1, max_length=36)
    monto: float = Field(gt=0)


class CrearReciboRequest(BaseModel):
    cliente_id: str = Field(min_length=1, max_length=36)
    fecha: date | None = None
    monto: float = Field(gt=0)
    medio: MedioCobro = "efectivo"
    observacion: str = Field(default="", max_length=200)
    imputaciones: list[CrearImputacionRequest] = Field(min_length=1)
