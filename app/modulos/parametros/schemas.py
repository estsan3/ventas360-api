"""DTOs del módulo parámetros."""

from typing import Literal

from pydantic import BaseModel, Field

TipoComprobanteTalonario = Literal["pedido", "remito", "factura"]


class ParametrosNegocio(BaseModel):
    """Parámetros comerciales (IVA, moneda)."""

    iva_porcentaje: float = Field(ge=0, le=100)
    moneda: Literal["ARS", "USD"]


class PreferenciasNotificacion(BaseModel):
    """Preferencias de notificación del equipo."""

    stock_bajo: bool
    venta_confirmada: bool
    cliente_nuevo: bool


class ParametrosOperativos(BaseModel):
    """Sucursal default y condiciones de pago (Fase A)."""

    sucursal_codigo: str = Field(default="CENTRAL", max_length=20)
    sucursal_nombre: str = Field(default="Casa central", max_length=120)
    # Lista separada por comas en persistencia; acá tipada.
    condiciones_pago: list[str] = Field(
        default_factory=lambda: ["contado", "30_dias", "60_dias"]
    )


class TalonarioResponse(BaseModel):
    id: str
    tipo_comprobante: TipoComprobanteTalonario
    prefijo: str
    proximo_numero: int
    activo: bool

    model_config = {"from_attributes": True}


class UpsertTalonarioRequest(BaseModel):
    tipo_comprobante: TipoComprobanteTalonario
    prefijo: str = Field(default="", max_length=20)
    proximo_numero: int = Field(default=1, ge=1)
    activo: bool = True


class NumeroAsignadoResponse(BaseModel):
    tipo_comprobante: str
    numero: str
