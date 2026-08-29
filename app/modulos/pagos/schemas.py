"""DTOs del módulo pagos."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from app.modulos.bancos.schemas import DatosChequeRequest

MedioPago = Literal["efectivo", "transferencia", "cheque"]
MedioPagoPersistido = Literal["efectivo", "transferencia", "cheque", "mixto"]


class LineaPagoResponse(BaseModel):
    id: str
    medio: str
    monto: float
    cheque_id: str = ""

    model_config = {"from_attributes": True}


class PagoResponse(BaseModel):
    id: str
    proveedor_id: str
    fecha: date
    monto: float
    medio: MedioPagoPersistido
    observacion: str
    lineas: list[LineaPagoResponse]

    model_config = {"from_attributes": True}


class CrearLineaPagoRequest(BaseModel):
    """efectivo / transferencia / cheque de cartera (cheque_id) / cheque propio (cheque)."""

    medio: MedioPago
    monto: float = Field(gt=0)
    cheque_id: str | None = Field(default=None, max_length=36)
    cheque: DatosChequeRequest | None = None


class CrearPagoRequest(BaseModel):
    proveedor_id: str = Field(min_length=1, max_length=36)
    monto: float = Field(gt=0)
    fecha: date | None = None
    observacion: str = Field(default="", max_length=200)
    destinatario: str = Field(default="", max_length=120)
    medio: MedioPago = "efectivo"
    cheque_id: str | None = Field(default=None, max_length=36)
    cheque: DatosChequeRequest | None = None
    medios: list[CrearLineaPagoRequest] | None = None
