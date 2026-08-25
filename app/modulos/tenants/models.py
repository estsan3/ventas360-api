"""Modelos ORM del módulo tenants. Prefijo de tabla: `tenants_`."""

import uuid

from sqlalchemy import Boolean, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.tenant_ctx import ConTenant


def _nuevo_id() -> str:
    return str(uuid.uuid4())


class Tenant(Base):
    """Comercio aislado (Ferretería AgroNorte, Kiosco Milka, …)."""

    __tablename__ = "tenants_tenant"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_nuevo_id)
    slug: Mapped[str] = mapped_column(String(48), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(120))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)


class PermisoRol(ConTenant, Base):
    """Celda de la matriz rol × módulo (solo vendedor y encargado)."""

    __tablename__ = "tenants_permiso_rol"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "rol", "modulo", name="uq_tenants_permiso_rol"
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_nuevo_id)
    rol: Mapped[str] = mapped_column(String(20), index=True)
    modulo: Mapped[str] = mapped_column(String(40))
    habilitado: Mapped[bool] = mapped_column(Boolean, default=True)
