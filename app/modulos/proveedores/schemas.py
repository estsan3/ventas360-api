"""DTOs del módulo proveedores."""

from typing import Literal

from pydantic import BaseModel, EmailStr, Field

from app.core.paginacion import PaginaResponse

CondicionIva = Literal[
    "responsable_inscripto",
    "monotributo",
    "exento",
    "consumidor_final",
]


class ProveedorResponse(BaseModel):
    id: str
    nombre: str
    email: str
    telefono: str
    cuit: str
    condicion_iva: CondicionIva
    observaciones: str
    activo: bool

    model_config = {"from_attributes": True}


class CrearProveedorRequest(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)
    email: EmailStr | str = ""
    telefono: str = Field(default="", max_length=40)
    cuit: str = Field(default="", max_length=13)
    condicion_iva: CondicionIva = "responsable_inscripto"
    observaciones: str = Field(default="", max_length=2000)


class ActualizarProveedorRequest(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=120)
    email: EmailStr | str | None = None
    telefono: str | None = Field(default=None, max_length=40)
    cuit: str | None = Field(default=None, max_length=13)
    condicion_iva: CondicionIva | None = None
    observaciones: str | None = Field(default=None, max_length=2000)


class ProveedoresPaginaResponse(PaginaResponse[ProveedorResponse]):
    """Listado paginado de proveedores."""
