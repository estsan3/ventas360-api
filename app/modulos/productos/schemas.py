"""DTOs del módulo productos."""

from pydantic import BaseModel, Field


class ProductoResponse(BaseModel):
    """Producto expuesto por la API."""

    id: str
    sku: str
    nombre: str
    precio: float
    stock: int
    activo: bool

    model_config = {"from_attributes": True}


class CrearProductoRequest(BaseModel):
    """Alta de producto."""

    sku: str = Field(min_length=1, max_length=40)
    nombre: str = Field(min_length=1, max_length=120)
    precio: float = Field(gt=0)
    stock: int = Field(ge=0, default=0)


class ActualizarProductoRequest(BaseModel):
    """Actualización parcial de producto."""

    sku: str | None = Field(default=None, min_length=1, max_length=40)
    nombre: str | None = Field(default=None, min_length=1, max_length=120)
    precio: float | None = Field(default=None, gt=0)
    stock: int | None = Field(default=None, ge=0)
    activo: bool | None = None
