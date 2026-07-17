"""DTOs del módulo bancos."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

TipoMovBancario = Literal["credito", "debito"]
TipoValor = Literal["cheque_tercero", "cheque_propio"]
EstadoValor = Literal["en_cartera", "depositado", "cobrado", "rechazado"]


class CuentaBancariaResponse(BaseModel):
    id: str
    codigo: str
    nombre: str
    banco: str
    cbu: str
    es_default: bool
    activo: bool
    saldo: float = 0.0

    model_config = {"from_attributes": True}


class CrearCuentaBancariaRequest(BaseModel):
    codigo: str = Field(min_length=1, max_length=20)
    nombre: str = Field(min_length=1, max_length=120)
    banco: str = Field(default="", max_length=80)
    cbu: str = Field(default="", max_length=22)
    es_default: bool = False


class MovimientoBancarioResponse(BaseModel):
    id: str
    cuenta_id: str
    fecha: date
    tipo: TipoMovBancario
    monto: float
    concepto: str
    referencia_tipo: str
    referencia_id: str

    model_config = {"from_attributes": True}


class ValorBancarioResponse(BaseModel):
    id: str
    tipo: TipoValor
    estado: EstadoValor
    monto: float
    fecha: date
    fecha_vto: date | None
    numero: str
    librador: str
    banco_emisor: str
    cuenta_destino_id: str | None
    observacion: str

    model_config = {"from_attributes": True}


class CrearValorRequest(BaseModel):
    tipo: TipoValor = "cheque_tercero"
    monto: float = Field(gt=0)
    fecha: date | None = None
    fecha_vto: date | None = None
    numero: str = Field(default="", max_length=40)
    librador: str = Field(default="", max_length=120)
    banco_emisor: str = Field(default="", max_length=80)
    observacion: str = Field(default="", max_length=200)


class DepositarValorRequest(BaseModel):
    cuenta_id: str | None = Field(default=None, max_length=36)
