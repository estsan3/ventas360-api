"""Modelos ORM del módulo proveedores. Prefijo: `proveedores_`."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _nuevo_id() -> str:
    return str(uuid.uuid4())


def _mapeo_default() -> list[dict[str, str]]:
    return [
        {"columna": "A", "campo": "codigo_producto"},
        {"columna": "B", "campo": "descripcion"},
        {"columna": "C", "campo": "precio_costo"},
    ]


class Proveedor(Base):
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
