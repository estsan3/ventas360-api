"""Modelos ORM del módulo clientes. Prefijo de tabla: `clientes_`."""

import uuid

from sqlalchemy import Boolean, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _nuevo_id() -> str:
    return str(uuid.uuid4())


class Cliente(Base):
    """Cliente del comercio (datos comerciales y fiscales básicos)."""

    __tablename__ = "clientes_cliente"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_nuevo_id)
    nombre: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(120), index=True)
    telefono: Mapped[str] = mapped_column(String(40), default="")
    cuit: Mapped[str] = mapped_column(String(13), default="")
    condicion_iva: Mapped[str] = mapped_column(String(40), default="consumidor_final")
    limite_credito: Mapped[float] = mapped_column(Float, default=0.0)
    zona_id: Mapped[str | None] = mapped_column(String(36), nullable=True, default=None)
    vendedor_id: Mapped[str | None] = mapped_column(String(36), nullable=True, default=None)
    bloqueado: Mapped[bool] = mapped_column(Boolean, default=False)
    observaciones: Mapped[str] = mapped_column(Text, default="")
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
