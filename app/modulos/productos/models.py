"""Modelos ORM del módulo productos. Prefijo de tabla: `productos_`."""

import uuid

from sqlalchemy import Boolean, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _nuevo_id() -> str:
    return str(uuid.uuid4())


class Producto(Base):
    """Artículo del catálogo.

    `precio` es el precio de lista vigente (Fase A). El stock plano se
    mantiene hasta que el módulo `stock` multi-depósito lo reemplace.
    """

    __tablename__ = "productos_producto"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_nuevo_id)
    sku: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(120), index=True)
    marca: Mapped[str] = mapped_column(String(80), default="")
    rubro: Mapped[str] = mapped_column(String(80), default="")
    codigo_barras: Mapped[str] = mapped_column(String(40), default="", index=True)
    costo: Mapped[float] = mapped_column(Float, default=0.0)
    precio: Mapped[float] = mapped_column(Float)
    stock: Mapped[int] = mapped_column(Integer, default=0)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
