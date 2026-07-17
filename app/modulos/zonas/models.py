"""Modelos ORM del módulo zonas. Prefijo: `zonas_`."""

import uuid

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _nuevo_id() -> str:
    return str(uuid.uuid4())


class Zona(Base):
    """Zona comercial para segmentar clientes."""

    __tablename__ = "zonas_zona"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_nuevo_id)
    nombre: Mapped[str] = mapped_column(String(80), unique=True)
    codigo: Mapped[str] = mapped_column(String(20), default="")
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
