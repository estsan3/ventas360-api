"""DTOs del módulo proveedores."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

from app.core.paginacion import PaginaResponse

CondicionIva = Literal[
    "responsable_inscripto",
    "monotributo",
    "exento",
    "consumidor_final",
]

PoliticaPrecioVenta = Literal["solo_costo", "margen_fijo", "copiar_lista"]

CampoMapeo = Literal[
    "codigo_producto",
    "descripcion",
    "precio_costo",
    "precio_lista",
    "marca",
    "rubro",
    "ignorar",
]


class MapeoColumna(BaseModel):
    columna: str = Field(min_length=1, max_length=20)
    campo: str = Field(min_length=1, max_length=40)


class ProveedorResponse(BaseModel):
    id: str
    nombre: str
    email: str
    telefono: str
    cuit: str
    condicion_iva: CondicionIva
    observaciones: str
    activo: bool
    mapeo_excel: list[MapeoColumna] = Field(default_factory=list)
    excel_fila_inicio: int = 2
    politica_precio_venta: PoliticaPrecioVenta = "solo_costo"
    margen_venta_pct: float = 30.0
    ultima_importacion_fecha: datetime | None = None
    ultima_importacion_archivo: str = ""
    ultima_importacion_actualizados: int = 0
    ultima_importacion_nuevos: int = 0
    ultima_importacion_sin_match: int = 0

    model_config = {"from_attributes": True}


class CrearProveedorRequest(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)
    email: EmailStr | str = ""
    telefono: str = Field(default="", max_length=40)
    cuit: str = Field(default="", max_length=13)
    condicion_iva: CondicionIva = "responsable_inscripto"
    observaciones: str = Field(default="", max_length=2000)
    mapeo_excel: list[MapeoColumna] | None = None
    excel_fila_inicio: int = Field(default=2, ge=1, le=1000)
    politica_precio_venta: PoliticaPrecioVenta = "solo_costo"
    margen_venta_pct: float = Field(default=30.0, ge=0, le=500)


class ActualizarProveedorRequest(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=120)
    email: EmailStr | str | None = None
    telefono: str | None = Field(default=None, max_length=40)
    cuit: str | None = Field(default=None, max_length=13)
    condicion_iva: CondicionIva | None = None
    observaciones: str | None = Field(default=None, max_length=2000)
    mapeo_excel: list[MapeoColumna] | None = None
    excel_fila_inicio: int | None = Field(default=None, ge=1, le=1000)
    politica_precio_venta: PoliticaPrecioVenta | None = None
    margen_venta_pct: float | None = Field(default=None, ge=0, le=500)


class ProveedoresPaginaResponse(PaginaResponse[ProveedorResponse]):
    """Listado paginado de proveedores."""


class ImportarListaResponse(BaseModel):
    proveedor_id: str
    archivo: str
    dry_run: bool
    actualizados: int
    nuevos: int
    sin_match: int
    omitidas: list[str] = Field(default_factory=list)
    sin_match_codigos: list[str] = Field(default_factory=list)
    preview_cols: list[str] = Field(default_factory=list)
    preview_rows: list[list[str]] = Field(default_factory=list)
