"""Modelos ORM del módulo stock. Prefijo: `stock_`."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.tenant_ctx import ConTenant


def _nuevo_id() -> str:
    return str(uuid.uuid4())


class Deposito(ConTenant, Base):
    """Depósito / almacén físico."""

    __tablename__ = "stock_deposito"
    __table_args__ = (
        UniqueConstraint("tenant_id", "codigo", name="uq_stock_deposito_codigo_tenant"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_nuevo_id)
    codigo: Mapped[str] = mapped_column(String(20), index=True)
    nombre: Mapped[str] = mapped_column(String(120))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)


class SaldoStock(ConTenant, Base):
    """Saldo por artículo y depósito (IDs débiles a productos)."""

    __tablename__ = "stock_saldo"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "articulo_id",
            "deposito_id",
            name="uq_stock_articulo_deposito",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_nuevo_id)
    articulo_id: Mapped[str] = mapped_column(String(36), index=True)
    deposito_id: Mapped[str] = mapped_column(String(36), index=True)
    cantidad: Mapped[int] = mapped_column(Integer, default=0)


class MovimientoStock(ConTenant, Base):
    """Movimiento de inventario (ajuste, egreso remito, etc.)."""

    __tablename__ = "stock_movimiento"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_nuevo_id)
    articulo_id: Mapped[str] = mapped_column(String(36), index=True)
    deposito_id: Mapped[str] = mapped_column(String(36), index=True)
    tipo: Mapped[str] = mapped_column(String(40))  # ajuste | egreso_remito | ingreso
    cantidad: Mapped[int] = mapped_column(Integer)  # signed: + ingreso, - egreso
    referencia: Mapped[str] = mapped_column(String(80), default="")
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
