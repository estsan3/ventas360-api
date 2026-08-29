"""DTOs del módulo parámetros."""

from typing import Literal

from pydantic import BaseModel, Field

TipoComprobanteTalonario = Literal["pedido", "remito", "factura"]
CondicionIvaEmisor = Literal["responsable_inscripto", "monotributo", "exento"]


class ParametrosNegocio(BaseModel):
    """Parámetros comerciales (IVA, moneda)."""

    iva_porcentaje: float = Field(ge=0, le=100)
    moneda: Literal["ARS", "USD"]


class ParametrosAfip(BaseModel):
    """Identidad fiscal del emisor (por comercio). Certificados van por env."""

    habilitada: bool = False
    cuit: str = Field(default="", max_length=13)
    razon_social: str = Field(default="", max_length=120)
    condicion_iva: CondicionIvaEmisor = "responsable_inscripto"
    punto_venta: int = Field(default=1, ge=1, le=99999)
    domicilio: str = Field(default="", max_length=200)


class ParametrosAfipResponse(ParametrosAfip):
    """Incluye el ambiente ARCA (solo lectura, viene del server)."""

    proveedor: Literal["simulado", "afip"] = "simulado"
    homologacion: bool = True
    certificado_configurado: bool = False


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
