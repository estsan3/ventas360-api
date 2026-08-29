"""Modelos ORM pagos. Prefijo: `pagos_`."""

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.tenant_ctx import ConTenant


def _nuevo_id() -> str:
    return str(uuid.uuid4())


class PagoProveedor(ConTenant, Base):
    """Pago a un proveedor: baja CxP e impacta caja / banco / cartera."""

    __tablename__ = "pagos_pago"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_nuevo_id)
    proveedor_id: Mapped[str] = mapped_column(String(36), index=True)
    fecha: Mapped[date] = mapped_column(Date)
    monto: Mapped[float] = mapped_column(Float)
    # efectivo | transferencia | cheque | mixto
    medio: Mapped[str] = mapped_column(String(20), default="efectivo")
    observacion: Mapped[str] = mapped_column(String(200), default="")
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    lineas: Mapped[list["LineaPago"]] = relationship(
        back_populates="pago", cascade="all, delete-orphan", lazy="selectin"
    )


class LineaPago(ConTenant, Base):
    """Medio de un pago (efectivo, transferencia o un cheque)."""

    __tablename__ = "pagos_linea"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_nuevo_id)
    pago_id: Mapped[str] = mapped_column(String(36), ForeignKey("pagos_pago.id"))
    medio: Mapped[str] = mapped_column(String(20))
    monto: Mapped[float] = mapped_column(Float)
    cheque_id: Mapped[str] = mapped_column(String(36), default="")

    pago: Mapped[PagoProveedor] = relationship(back_populates="lineas")
