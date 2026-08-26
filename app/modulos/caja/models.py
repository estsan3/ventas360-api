"""Modelos ORM caja. Prefijo: `caja_`."""

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.tenant_ctx import ConTenant


def _nuevo_id() -> str:
    return str(uuid.uuid4())


class MovimientoCaja(ConTenant, Base):
    """Movimiento de caja (efectivo / tarjeta stub / egresos)."""

    __tablename__ = "caja_movimiento"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_nuevo_id)
    fecha: Mapped[date] = mapped_column(Date, index=True)
    # ingreso | egreso
    tipo: Mapped[str] = mapped_column(String(10))
    # efectivo | tarjeta | cheque | otro
    medio: Mapped[str] = mapped_column(String(20), default="efectivo")
    monto: Mapped[float] = mapped_column(Float)
    concepto: Mapped[str] = mapped_column(String(200), default="")
    referencia_tipo: Mapped[str] = mapped_column(String(20), default="")
    referencia_id: Mapped[str] = mapped_column(String(36), default="", index=True)
    sesion_id: Mapped[str] = mapped_column(String(36), default="", index=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class SesionCaja(ConTenant, Base):
    """Turno de caja: se puede abrir otro el mismo día después de cerrar."""

    __tablename__ = "caja_sesion"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_nuevo_id)
    fecha: Mapped[date] = mapped_column(Date, index=True)
    # abierta | cerrada
    estado: Mapped[str] = mapped_column(String(12), default="abierta")
    fondo_inicial: Mapped[float] = mapped_column(Float, default=0.0)
    efectivo_esperado: Mapped[float | None] = mapped_column(Float, nullable=True)
    efectivo_contado: Mapped[float | None] = mapped_column(Float, nullable=True)
    diferencia: Mapped[float | None] = mapped_column(Float, nullable=True)
    cheques_esperado: Mapped[float | None] = mapped_column(Float, nullable=True)
    cheques_contado: Mapped[float | None] = mapped_column(Float, nullable=True)
    cheques_diferencia: Mapped[float | None] = mapped_column(Float, nullable=True)
    tarjetas_esperado: Mapped[float | None] = mapped_column(Float, nullable=True)
    tarjetas_contado: Mapped[float | None] = mapped_column(Float, nullable=True)
    tarjetas_diferencia: Mapped[float | None] = mapped_column(Float, nullable=True)
    abierta_por: Mapped[str] = mapped_column(String(120), default="")
    cerrada_por: Mapped[str] = mapped_column(String(120), default="")
    abierta_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    cerrada_en: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
