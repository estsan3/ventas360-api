"""DTOs del módulo parámetros: dan forma tipada al almacén clave/valor."""

from typing import Literal

from pydantic import BaseModel, Field


class ParametrosNegocio(BaseModel):
    """Parámetros comerciales que usa el front en gestión y reportería."""

    iva_porcentaje: float = Field(ge=0, le=100)
    moneda: Literal["ARS", "USD"]


class PreferenciasNotificacion(BaseModel):
    """Qué avisos quiere recibir el equipo admin."""

    stock_bajo: bool
    venta_confirmada: bool
    cliente_nuevo: bool
