"""Modelos ORM del módulo precios. Prefijo: `precios_`."""

import uuid

from sqlalchemy import Boolean, Float, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _nuevo_id() -> str:
    return str(uuid.uuid4())


class ListaPrecio(Base):
    """Lista de precios (mayorista, minorista, etc.)."""

    __tablename__ = "precios_lista"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_nuevo_id)
    codigo: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(120))
    es_default: Mapped[bool] = mapped_column(Boolean, default=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)


class PrecioArticulo(Base):
    """Precio de un artículo en una lista (ID débil a productos)."""

    __tablename__ = "precios_articulo"
    __table_args__ = (
        UniqueConstraint("lista_id", "articulo_id", name="uq_precios_lista_articulo"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_nuevo_id)
    lista_id: Mapped[str] = mapped_column(String(36), index=True)
    articulo_id: Mapped[str] = mapped_column(String(36), index=True)
    precio: Mapped[float] = mapped_column(Float)
