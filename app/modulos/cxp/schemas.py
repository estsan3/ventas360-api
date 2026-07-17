"""DTOs CxP."""

from datetime import date

from pydantic import BaseModel


class MovimientoCxpResponse(BaseModel):
    id: str
    proveedor_id: str
    tipo: str
    monto: float
    referencia_tipo: str
    referencia_id: str
    concepto: str
    fecha: date

    model_config = {"from_attributes": True}


class SaldoProveedorResponse(BaseModel):
    proveedor_id: str
    debe: float
    haber: float
    saldo: float


class EstadoCuentaProveedorResponse(BaseModel):
    proveedor_id: str
    saldo: float
    movimientos: list[MovimientoCxpResponse]
