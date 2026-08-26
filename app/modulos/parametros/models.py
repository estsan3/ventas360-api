"""Modelos ORM del módulo parámetros. Prefijo de tabla: `parametros_`."""

import uuid

from sqlalchemy import Boolean, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.tenant_ctx import ConTenant


def _nuevo_id() -> str:
    return str(uuid.uuid4())


class Parametro(ConTenant, Base):
    """Parámetro de configuración por comercio (clave/valor)."""

    __tablename__ = "parametros_parametro"
    __table_args__ = (
        UniqueConstraint("tenant_id", "clave", name="uq_parametros_clave_tenant"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_nuevo_id)
    clave: Mapped[str] = mapped_column(String(60), index=True)
    valor: Mapped[str] = mapped_column(Text, default="")


class Talonario(ConTenant, Base):
    """Numerador / talonario por tipo de comprobante y comercio."""

    __tablename__ = "parametros_talonario"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "tipo_comprobante", name="uq_parametros_talonario_tenant"
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_nuevo_id)
    # pedido | remito | factura | presupuesto
    tipo_comprobante: Mapped[str] = mapped_column(String(20), index=True)
    prefijo: Mapped[str] = mapped_column(String(20), default="")
    proximo_numero: Mapped[int] = mapped_column(Integer, default=1)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
