"""Modelos ORM del módulo clientes. Prefijo de tabla: `clientes_`."""

import uuid

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _nuevo_id() -> str:
    return str(uuid.uuid4())


class Cliente(Base):
    """Cliente del comercio."""

    __tablename__ = "clientes_cliente"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_nuevo_id)
    nombre: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(120), index=True)
    telefono: Mapped[str] = mapped_column(String(40), default="")
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
