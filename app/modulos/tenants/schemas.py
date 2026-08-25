"""DTOs del módulo tenants."""

from typing import Literal

from pydantic import BaseModel, EmailStr, Field

TipoContextoHost = Literal["plataforma", "comercio", "sin_slug"]


class TenantPublico(BaseModel):
    """Datos seguros para mostrar en login (nombre en la pantalla)."""

    id: str
    slug: str
    nombre: str

    model_config = {"from_attributes": True}


class TenantResponse(BaseModel):
    id: str
    slug: str
    nombre: str
    activo: bool

    model_config = {"from_attributes": True}


class AdministradorInicialRequest(BaseModel):
    """Primer administrador del comercio (lo crea la plataforma)."""

    nombre: str = Field(min_length=2, max_length=120)
    dni: str = Field(min_length=6, max_length=20)
    email: EmailStr
    password: str | None = Field(default=None, min_length=8)


class CrearTenantRequest(BaseModel):
    """Alta de comercio + primer administrador. El slug no se edita después."""

    nombre: str = Field(min_length=1, max_length=120)
    slug: str = Field(min_length=1, max_length=48)
    administrador: AdministradorInicialRequest


class ActualizarTenantRequest(BaseModel):
    """Nombre comercial y activo. El slug es de solo lectura."""

    nombre: str | None = Field(default=None, min_length=1, max_length=120)
    activo: bool | None = None


class AdministradorCreadoResponse(BaseModel):
    id: str
    nombre: str
    email: str
    rol: str


class TenantCreadoResponse(TenantResponse):
    administrador: AdministradorCreadoResponse


class ContextoHostResponse(BaseModel):
    """Qué comercio (o plataforma) corresponde al Host/Origin actual."""

    tipo: TipoContextoHost
    slug: str | None = None
    tenant: TenantPublico | None = None
