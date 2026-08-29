"""Modelos ORM del módulo proveedores. Prefijo: `proveedores_`."""

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.tenant_ctx import ConTenant


def _nuevo_id() -> str:
    return str(uuid.uuid4())


def _mapeo_default() -> list[dict[str, str]]:
    return [
        {"columna": "A", "campo": "codigo_producto"},
        {"columna": "B", "campo": "descripcion"},
        {"columna": "C", "campo": "precio_costo"},
    ]


class Proveedor(ConTenant, Base):
    """Proveedor del comercio."""

    __tablename__ = "proveedores_proveedor"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_nuevo_id)
    nombre: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(120), default="", index=True)
    telefono: Mapped[str] = mapped_column(String(40), default="")
    cuit: Mapped[str] = mapped_column(String(13), default="")
    condicion_iva: Mapped[str] = mapped_column(String(40), default="responsable_inscripto")
    observaciones: Mapped[str] = mapped_column(Text, default="")
    activo: Mapped[bool] = mapped_column(Boolean, default=True)

    # Formato de lista Excel (persistido por proveedor)
    mapeo_excel: Mapped[list] = mapped_column(JSON, default=_mapeo_default)
    excel_fila_inicio: Mapped[int] = mapped_column(Integer, default=2)
    politica_precio_venta: Mapped[str] = mapped_column(String(40), default="solo_costo")
    margen_venta_pct: Mapped[float] = mapped_column(Float, default=30.0)

    # Última importación (estadísticas)
    ultima_importacion_fecha: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ultima_importacion_archivo: Mapped[str] = mapped_column(String(255), default="")
    ultima_importacion_actualizados: Mapped[int] = mapped_column(Integer, default=0)
    ultima_importacion_nuevos: Mapped[int] = mapped_column(Integer, default=0)
    ultima_importacion_sin_match: Mapped[int] = mapped_column(Integer, default=0)


class ListaProveedorItem(ConTenant, Base):
    """Fila de la lista de precios del proveedor (no es el catálogo)."""

    __tablename__ = "proveedores_lista_item"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "proveedor_id",
            "codigo_proveedor",
            name="uq_prov_lista_codigo_tenant",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_nuevo_id)
    proveedor_id: Mapped[str] = mapped_column(String(36), index=True)
    codigo_proveedor: Mapped[str] = mapped_column(String(40), index=True)
    nombre: Mapped[str] = mapped_column(String(120), default="")
    costo: Mapped[float] = mapped_column(Float, default=0.0)
    precio_lista: Mapped[float] = mapped_column(Float, default=0.0)
    marca: Mapped[str] = mapped_column(String(80), default="")
    rubro: Mapped[str] = mapped_column(String(80), default="")
    articulo_id: Mapped[str] = mapped_column(String(36), default="", index=True)
