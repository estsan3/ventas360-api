"""Modelos ORM del módulo productos. Prefijo de tabla: `productos_`."""

import uuid

from sqlalchemy import Boolean, Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.tenant_ctx import ConTenant


def _nuevo_id() -> str:
    return str(uuid.uuid4())


class Producto(ConTenant, Base):
    """Artículo del catálogo.

    `precio` es el precio de lista vigente (Fase A). El stock plano se
    mantiene hasta que el módulo `stock` multi-depósito lo reemplace.
    """

    __tablename__ = "productos_producto"
    __table_args__ = (
        UniqueConstraint("tenant_id", "sku", name="uq_productos_sku_tenant"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_nuevo_id)
    sku: Mapped[str] = mapped_column(String(40), index=True)
    nombre: Mapped[str] = mapped_column(String(120), index=True)
    marca: Mapped[str] = mapped_column(String(80), default="")
    rubro: Mapped[str] = mapped_column(String(80), default="")
    codigo_barras: Mapped[str] = mapped_column(String(40), default="", index=True)
    costo: Mapped[float] = mapped_column(Float, default=0.0)
    precio: Mapped[float] = mapped_column(Float)
    stock: Mapped[int] = mapped_column(Integer, default=0)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
