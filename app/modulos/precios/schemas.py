"""DTOs del módulo precios."""

from pydantic import BaseModel, Field


class ListaPrecioResponse(BaseModel):
    id: str
    codigo: str
    nombre: str
    es_default: bool
    activo: bool

    model_config = {"from_attributes": True}


class CrearListaPrecioRequest(BaseModel):
    codigo: str = Field(min_length=1, max_length=20)
    nombre: str = Field(min_length=1, max_length=120)
    es_default: bool = False


class ActualizarListaPrecioRequest(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=120)
    es_default: bool | None = None


class PrecioArticuloResponse(BaseModel):
    id: str
    lista_id: str
    articulo_id: str
    precio: float

    model_config = {"from_attributes": True}


class UpsertPrecioArticuloRequest(BaseModel):
    lista_id: str = Field(min_length=1, max_length=36)
    articulo_id: str = Field(min_length=1, max_length=36)
    precio: float = Field(gt=0)


class PrecioResueltoResponse(BaseModel):
    articulo_id: str
    cliente_id: str | None
    lista_id: str | None
    precio: float
    origen: str  # lista | catalogo
