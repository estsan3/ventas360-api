"""DTOs del módulo productos."""

from pydantic import BaseModel, Field

from app.core.paginacion import PaginaResponse


class ProductoResponse(BaseModel):
    """Producto expuesto por la API."""

    id: str
    sku: str
    nombre: str
    marca: str
    rubro: str
    codigo_barras: str
    costo: float
    precio: float
    stock: int
    activo: bool

    model_config = {"from_attributes": True}


class CrearProductoRequest(BaseModel):
    """Alta de producto."""

    sku: str = Field(min_length=1, max_length=40)
    nombre: str = Field(min_length=1, max_length=120)
    marca: str = Field(default="", max_length=80)
    rubro: str = Field(default="", max_length=80)
    codigo_barras: str = Field(default="", max_length=40)
    costo: float = Field(default=0.0, ge=0)
    precio: float = Field(gt=0)
    stock: int = Field(ge=0, default=0)


class ActualizarProductoRequest(BaseModel):
    """Actualización parcial de producto."""

    sku: str | None = Field(default=None, min_length=1, max_length=40)
    nombre: str | None = Field(default=None, min_length=1, max_length=120)
    marca: str | None = Field(default=None, max_length=80)
    rubro: str | None = Field(default=None, max_length=80)
    codigo_barras: str | None = Field(default=None, max_length=40)
    costo: float | None = Field(default=None, ge=0)
    precio: float | None = Field(default=None, gt=0)
    stock: int | None = Field(default=None, ge=0)
    activo: bool | None = None


class ProductosPaginaResponse(PaginaResponse[ProductoResponse]):
    """Listado paginado de productos."""
