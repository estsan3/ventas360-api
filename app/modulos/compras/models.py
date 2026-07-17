"""Modelos ORM compras. Prefijo: `compras_`."""

import uuid
from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _nuevo_id() -> str:
    return str(uuid.uuid4())


class Compra(Base):
    """Comprobante de compra tipado (remito_compra | factura_compra)."""

    __tablename__ = "compras_compra"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_nuevo_id)
    tipo: Mapped[str] = mapped_column(String(20), index=True)
    proveedor_id: Mapped[str] = mapped_column(String(36), index=True)
    estado: Mapped[str] = mapped_column(String(20), default="borrador")
    deposito_id: Mapped[str | None] = mapped_column(String(36), nullable=True, default=None)
    origen_id: Mapped[str | None] = mapped_column(String(36), nullable=True, default=None)
    neto: Mapped[float] = mapped_column(Float, default=0.0)
    iva: Mapped[float] = mapped_column(Float, default=0.0)
    total: Mapped[float] = mapped_column(Float, default=0.0)
    iva_porcentaje: Mapped[float] = mapped_column(Float, default=21.0)
    numero: Mapped[str | None] = mapped_column(String(40), nullable=True, default=None)
    fecha: Mapped[date] = mapped_column(Date)

    lineas: Mapped[list["LineaCompra"]] = relationship(
        back_populates="compra", cascade="all, delete-orphan", lazy="selectin"
    )


class LineaCompra(Base):
    __tablename__ = "compras_linea"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_nuevo_id)
    compra_id: Mapped[str] = mapped_column(String(36), ForeignKey("compras_compra.id"))
    producto_id: Mapped[str] = mapped_column(String(36))
    descripcion: Mapped[str] = mapped_column(String(120), default="")
    cantidad: Mapped[int] = mapped_column(Integer)
    precio_unitario: Mapped[float] = mapped_column(Float)

    compra: Mapped[Compra] = relationship(back_populates="lineas")
