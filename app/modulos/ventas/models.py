"""Modelos ORM del módulo ventas. Prefijo de tabla: `ventas_`.

`Pedido` es el comprobante tipado (pedido | remito | factura). Se mantiene
el nombre de tabla `ventas_pedido` para no romper el scaffold.
Referencias a clientes/productos/depósitos como IDs débiles.
"""

import uuid
from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _nuevo_id() -> str:
    return str(uuid.uuid4())


class Pedido(Base):
    """Comprobante de venta tipado."""

    __tablename__ = "ventas_pedido"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_nuevo_id)
    # pedido | remito | factura
    tipo: Mapped[str] = mapped_column(String(20), default="pedido", index=True)
    cliente_id: Mapped[str] = mapped_column(String(36), index=True)
    # Estados según tipo (ver VentasBO)
    estado: Mapped[str] = mapped_column(String(20), default="borrador")
    deposito_id: Mapped[str | None] = mapped_column(String(36), nullable=True, default=None)
    origen_id: Mapped[str | None] = mapped_column(String(36), nullable=True, default=None)
    neto: Mapped[float] = mapped_column(Float, default=0.0)
    iva: Mapped[float] = mapped_column(Float, default=0.0)
    total: Mapped[float] = mapped_column(Float, default=0.0)
    iva_porcentaje: Mapped[float] = mapped_column(Float, default=21.0)
    cae: Mapped[str | None] = mapped_column(String(40), nullable=True, default=None)
    fecha: Mapped[date] = mapped_column(Date)

    lineas: Mapped[list["LineaPedido"]] = relationship(
        back_populates="pedido", cascade="all, delete-orphan", lazy="selectin"
    )


class LineaPedido(Base):
    """Línea de comprobante (snapshot de precio/cantidad)."""

    __tablename__ = "ventas_linea"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_nuevo_id)
    pedido_id: Mapped[str] = mapped_column(String(36), ForeignKey("ventas_pedido.id"))
    producto_id: Mapped[str] = mapped_column(String(36))
    descripcion: Mapped[str] = mapped_column(String(120), default="")
    cantidad: Mapped[int] = mapped_column(Integer)
    precio_unitario: Mapped[float] = mapped_column(Float)

    pedido: Mapped[Pedido] = relationship(back_populates="lineas")
