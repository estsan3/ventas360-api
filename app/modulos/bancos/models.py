"""Modelos ORM bancos. Prefijo: `bancos_`."""

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _nuevo_id() -> str:
    return str(uuid.uuid4())


class CuentaBancaria(Base):
    """Cuenta bancaria de la empresa."""

    __tablename__ = "bancos_cuenta"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_nuevo_id)
    codigo: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(120))
    banco: Mapped[str] = mapped_column(String(80), default="")
    cbu: Mapped[str] = mapped_column(String(22), default="")
    es_default: Mapped[bool] = mapped_column(Boolean, default=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)


class MovimientoBancario(Base):
    """Crédito/débito sobre una cuenta."""

    __tablename__ = "bancos_movimiento"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_nuevo_id)
    cuenta_id: Mapped[str] = mapped_column(String(36), index=True)
    fecha: Mapped[date] = mapped_column(Date, index=True)
    # credito | debito
    tipo: Mapped[str] = mapped_column(String(10))
    monto: Mapped[float] = mapped_column(Float)
    concepto: Mapped[str] = mapped_column(String(200), default="")
    referencia_tipo: Mapped[str] = mapped_column(String(20), default="")
    referencia_id: Mapped[str] = mapped_column(String(36), default="", index=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ValorBancario(Base):
    """Cheque / valor en cartera (liviano)."""

    __tablename__ = "bancos_valor"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_nuevo_id)
    # cheque_tercero | cheque_propio
    tipo: Mapped[str] = mapped_column(String(20))
    # en_cartera | depositado | cobrado | rechazado
    estado: Mapped[str] = mapped_column(String(20), default="en_cartera")
    monto: Mapped[float] = mapped_column(Float)
    fecha: Mapped[date] = mapped_column(Date)
    fecha_vto: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)
    numero: Mapped[str] = mapped_column(String(40), default="")
    librador: Mapped[str] = mapped_column(String(120), default="")
    banco_emisor: Mapped[str] = mapped_column(String(80), default="")
    cuenta_destino_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, default=None
    )
    observacion: Mapped[str] = mapped_column(String(200), default="")
