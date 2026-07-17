"""Modelos ORM del módulo cxc. Prefijo: `cxc_`."""

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _nuevo_id() -> str:
    return str(uuid.uuid4())


class MovimientoCxc(Base):
    """Movimiento de cuenta corriente (debe aumenta deuda, haber la reduce)."""

    __tablename__ = "cxc_movimiento"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_nuevo_id)
    cliente_id: Mapped[str] = mapped_column(String(36), index=True)
    # debe | haber
    tipo: Mapped[str] = mapped_column(String(10))
    monto: Mapped[float] = mapped_column(Float)
    # remito | factura | recibo | ajuste
    referencia_tipo: Mapped[str] = mapped_column(String(20), default="")
    referencia_id: Mapped[str] = mapped_column(String(36), default="", index=True)
    concepto: Mapped[str] = mapped_column(String(200), default="")
    fecha: Mapped[date] = mapped_column(Date)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
