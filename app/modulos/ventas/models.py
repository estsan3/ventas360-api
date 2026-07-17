"""Modelos ORM del módulo ventas. Prefijo de tabla: `ventas_`.

Referencias a clientes y productos como IDs débiles (sin ForeignKey
entre módulos). La FK pedido_id en líneas es interna al módulo.
"""

import uuid
from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _nuevo_id() -> str:
    return str(uuid.uuid4())


class Pedido(Base):
    """Pedido de venta."""

    __tablename__ = "ventas_pedido"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_nuevo_id)
    cliente_id: Mapped[str] = mapped_column(String(36))
    # Estados: borrador | confirmado | entregado | cancelado
    estado: Mapped[str] = mapped_column(String(20), default="borrador")
    total: Mapped[float] = mapped_column(Float, default=0.0)
    fecha: Mapped[date] = mapped_column(Date)

    lineas: Mapped[list["LineaPedido"]] = relationship(
        back_populates="pedido", cascade="all, delete-orphan", lazy="selectin"
    )


class LineaPedido(Base):
    """Línea de un pedido."""

    __tablename__ = "ventas_linea"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_nuevo_id)
    pedido_id: Mapped[str] = mapped_column(String(36), ForeignKey("ventas_pedido.id"))
    producto_id: Mapped[str] = mapped_column(String(36))
    cantidad: Mapped[int] = mapped_column(Integer)
    precio_unitario: Mapped[float] = mapped_column(Float)

    pedido: Mapped[Pedido] = relationship(back_populates="lineas")
