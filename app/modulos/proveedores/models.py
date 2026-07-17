"""Modelos ORM del módulo proveedores. Prefijo: `proveedores_`."""

import uuid

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _nuevo_id() -> str:
    return str(uuid.uuid4())


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
