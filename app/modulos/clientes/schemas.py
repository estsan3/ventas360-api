"""DTOs del módulo clientes."""

from typing import Literal

from pydantic import BaseModel, EmailStr, Field

from app.core.paginacion import PaginaResponse

CondicionIva = Literal[
    "responsable_inscripto",
    "monotributo",
    "exento",
    "consumidor_final",
]


class ClienteResponse(BaseModel):
    """Cliente expuesto por la API."""

    id: str
    nombre: str
    email: EmailStr
    telefono: str
    cuit: str
    condicion_iva: CondicionIva
    limite_credito: float
    zona_id: str | None
    vendedor_id: str | None
    bloqueado: bool
    observaciones: str
    activo: bool

    model_config = {"from_attributes": True}


class CrearClienteRequest(BaseModel):
    """Alta de cliente."""

    nombre: str = Field(min_length=1, max_length=120)
    email: EmailStr
    telefono: str = Field(default="", max_length=40)
    cuit: str = Field(default="", max_length=13)
    condicion_iva: CondicionIva = "consumidor_final"
    limite_credito: float = Field(default=0.0, ge=0)
    zona_id: str | None = Field(default=None, max_length=36)
    vendedor_id: str | None = Field(default=None, max_length=36)
    bloqueado: bool = False
    observaciones: str = Field(default="", max_length=2000)


class ActualizarClienteRequest(BaseModel):
    """Actualización parcial de cliente."""

    nombre: str | None = Field(default=None, min_length=1, max_length=120)
    email: EmailStr | None = None
    telefono: str | None = Field(default=None, max_length=40)
    cuit: str | None = Field(default=None, max_length=13)
    condicion_iva: CondicionIva | None = None
    limite_credito: float | None = Field(default=None, ge=0)
    zona_id: str | None = Field(default=None, max_length=36)
    vendedor_id: str | None = Field(default=None, max_length=36)
    bloqueado: bool | None = None
    observaciones: str | None = Field(default=None, max_length=2000)


class ClientesPaginaResponse(PaginaResponse[ClienteResponse]):
    """Listado paginado de clientes."""
