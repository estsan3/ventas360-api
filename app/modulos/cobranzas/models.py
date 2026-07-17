"""Modelos ORM del módulo cobranzas. Prefijo: `cobranzas_`."""

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _nuevo_id() -> str:
    return str(uuid.uuid4())


class Recibo(Base):
    """Recibo de cobranza a cliente."""

    __tablename__ = "cobranzas_recibo"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_nuevo_id)
    cliente_id: Mapped[str] = mapped_column(String(36), index=True)
    fecha: Mapped[date] = mapped_column(Date)
    monto: Mapped[float] = mapped_column(Float)
    # efectivo | transferencia | tarjeta
    medio: Mapped[str] = mapped_column(String(20), default="efectivo")
    observacion: Mapped[str] = mapped_column(String(200), default="")
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    imputaciones: Mapped[list["ImputacionRecibo"]] = relationship(
        back_populates="recibo", cascade="all, delete-orphan", lazy="selectin"
    )


class ImputacionRecibo(Base):
    """Imputación de un recibo a una factura (ID débil)."""

    __tablename__ = "cobranzas_imputacion"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_nuevo_id)
    recibo_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cobranzas_recibo.id")
    )
    factura_id: Mapped[str] = mapped_column(String(36), index=True)
    monto: Mapped[float] = mapped_column(Float)

    recibo: Mapped[Recibo] = relationship(back_populates="imputaciones")
