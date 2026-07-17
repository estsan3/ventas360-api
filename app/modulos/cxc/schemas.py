"""DTOs del módulo cxc."""

from datetime import date, datetime

from pydantic import BaseModel, Field


class MovimientoCxcResponse(BaseModel):
    id: str
    cliente_id: str
    tipo: str
    monto: float
    referencia_tipo: str
    referencia_id: str
    concepto: str
    fecha: date
    creado_en: datetime | None = None

    model_config = {"from_attributes": True}


class SaldoClienteResponse(BaseModel):
    cliente_id: str
    saldo: float
    debe_total: float
    haber_total: float
    fecha_ultimo_movimiento: date | None = None
    fecha_debe_mas_antigua: date | None = None


class EstadoCuentaResponse(BaseModel):
    cliente_id: str
    saldo: float
    movimientos: list[MovimientoCxcResponse]


class RegistrarMovimientoRequest(BaseModel):
    """Ajuste manual (admin)."""

    cliente_id: str = Field(min_length=1, max_length=36)
    tipo: str = Field(pattern="^(debe|haber)$")
    monto: float = Field(gt=0)
    concepto: str = Field(default="Ajuste", max_length=200)
    fecha: date | None = None
