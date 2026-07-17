"""Modelos ORM del módulo parámetros. Prefijo de tabla: `parametros_`."""

import uuid

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _nuevo_id() -> str:
    return str(uuid.uuid4())


class Parametro(Base):
    """Parámetro de configuración global (clave/valor)."""

    __tablename__ = "parametros_parametro"

    clave: Mapped[str] = mapped_column(String(60), primary_key=True)
    valor: Mapped[str] = mapped_column(Text, default="")


class Talonario(Base):
    """Numerador / talonario por tipo de comprobante."""

    __tablename__ = "parametros_talonario"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_nuevo_id)
    # pedido | remito | factura
    tipo_comprobante: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    prefijo: Mapped[str] = mapped_column(String(20), default="")
    proximo_numero: Mapped[int] = mapped_column(Integer, default=1)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
