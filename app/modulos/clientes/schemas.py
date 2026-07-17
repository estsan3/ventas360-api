"""DTOs del módulo clientes."""

from pydantic import BaseModel, EmailStr, Field


class ClienteResponse(BaseModel):
    """Cliente expuesto por la API."""

    id: str
    nombre: str
    email: EmailStr
    telefono: str
    activo: bool

    model_config = {"from_attributes": True}


class CrearClienteRequest(BaseModel):
    """Alta de cliente."""

    nombre: str = Field(min_length=1, max_length=120)
    email: EmailStr
    telefono: str = Field(default="", max_length=40)


class ActualizarClienteRequest(BaseModel):
    """Actualización parcial de cliente."""

    nombre: str | None = Field(default=None, min_length=1, max_length=120)
    email: EmailStr | None = None
    telefono: str | None = Field(default=None, max_length=40)
