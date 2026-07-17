"""DTOs del módulo zonas."""

from pydantic import BaseModel, Field

from app.core.paginacion import PaginaResponse


class ZonaResponse(BaseModel):
    id: str
    nombre: str
    codigo: str
    activo: bool

    model_config = {"from_attributes": True}


class CrearZonaRequest(BaseModel):
    nombre: str = Field(min_length=1, max_length=80)
    codigo: str = Field(default="", max_length=20)


class ActualizarZonaRequest(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=80)
    codigo: str | None = Field(default=None, max_length=20)


class ZonasPaginaResponse(PaginaResponse[ZonaResponse]):
    """Listado paginado de zonas."""
