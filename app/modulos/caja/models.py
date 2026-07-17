"""Modelos ORM caja. Prefijo: `caja_`."""

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _nuevo_id() -> str:
    return str(uuid.uuid4())


class MovimientoCaja(Base):
    """Movimiento de caja (efectivo / tarjeta stub / egresos)."""

    __tablename__ = "caja_movimiento"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_nuevo_id)
    fecha: Mapped[date] = mapped_column(Date, index=True)
    # ingreso | egreso
    tipo: Mapped[str] = mapped_column(String(10))
    # efectivo | tarjeta | otro
    medio: Mapped[str] = mapped_column(String(20), default="efectivo")
    monto: Mapped[float] = mapped_column(Float)
    concepto: Mapped[str] = mapped_column(String(200), default="")
    referencia_tipo: Mapped[str] = mapped_column(String(20), default="")
    referencia_id: Mapped[str] = mapped_column(String(36), default="", index=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
