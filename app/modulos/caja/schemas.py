"""DTOs del módulo caja."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

TipoCaja = Literal["ingreso", "egreso"]
MedioCaja = Literal["efectivo", "tarjeta", "cheque", "otro"]
EstadoCaja = Literal["sin_abrir", "abierta", "cerrada"]


class MovimientoCajaResponse(BaseModel):
    id: str
    fecha: date
    tipo: TipoCaja
    medio: MedioCaja
    monto: float
    concepto: str
    referencia_tipo: str
    referencia_id: str
    creado_en: datetime | None = None

    model_config = {"from_attributes": True}


class SaldoCajaResponse(BaseModel):
    fecha: date
    ingresos: float
    egresos: float
    saldo: float
    efectivo_esperado: float = 0
    estado: EstadoCaja = "sin_abrir"
    fondo_inicial: float = 0
    efectivo_contado: float | None = None
    diferencia: float | None = None
    cheques_esperado: float = 0
    cheques_contado: float | None = None
    cheques_diferencia: float | None = None
    tarjetas_esperado: float = 0
    tarjetas_contado: float | None = None
    tarjetas_diferencia: float | None = None
    abierta_por: str = ""
    cerrada_por: str = ""
    abierta_en: datetime | None = None
    cerrada_en: datetime | None = None


class ChequeCajaRequest(BaseModel):
    numero: str = Field(min_length=1, max_length=40)
    banco_emisor: str = Field(min_length=1, max_length=80)
    librador: str = Field(default="", max_length=120)
    fecha: date | None = None
    fecha_vto: date | None = None
    recibido_de: str = Field(default="", max_length=120)
    destinatario: str = Field(default="", max_length=120)


class CrearMovimientoCajaRequest(BaseModel):
    tipo: TipoCaja
    medio: MedioCaja = "efectivo"
    monto: float = Field(gt=0)
    concepto: str = Field(default="", max_length=200)
    fecha: date | None = None
    cheque_id: str | None = Field(default=None, max_length=36)
    cheque: ChequeCajaRequest | None = None
    entregado_a: str = Field(default="", max_length=120)


class AbrirCajaRequest(BaseModel):
    fondo_inicial: float = Field(default=0, ge=0)
    fecha: date | None = None


class CerrarCajaRequest(BaseModel):
    efectivo_contado: float = Field(ge=0)
    cheques_contado: float = Field(default=0, ge=0)
    tarjetas_contado: float = Field(default=0, ge=0)
    fecha: date | None = None
