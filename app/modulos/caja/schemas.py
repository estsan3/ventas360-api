"""DTOs del módulo caja."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

TipoCaja = Literal["ingreso", "egreso"]
MedioCaja = Literal["efectivo", "tarjeta", "otro"]


class MovimientoCajaResponse(BaseModel):
    id: str
    fecha: date
    tipo: TipoCaja
    medio: MedioCaja
    monto: float
    concepto: str
    referencia_tipo: str
    referencia_id: str

    model_config = {"from_attributes": True}


class SaldoCajaResponse(BaseModel):
    fecha: date
    ingresos: float
    egresos: float
    saldo: float


class CrearMovimientoCajaRequest(BaseModel):
    tipo: TipoCaja
    medio: MedioCaja = "efectivo"
    monto: float = Field(gt=0)
    concepto: str = Field(default="", max_length=200)
    fecha: date | None = None
