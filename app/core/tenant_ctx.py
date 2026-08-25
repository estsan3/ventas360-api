"""Tenant de la petición: ContextVar + columna ORM (infraestructura).

No es lógica de negocio: solo el ID débil del comercio actual.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.excepciones import ReglaDeNegocioViolada

_tenant_id: ContextVar[str | None] = ContextVar("ventas360_tenant_id", default=None)


def tenant_id_actual() -> str:
    """Tenant de la petición o del seed. Falla si no hay comercio."""
    valor = _tenant_id.get()
    if not valor:
        raise ReglaDeNegocioViolada("No hay comercio en el contexto")
    return valor


def tenant_id_opcional() -> str | None:
    return _tenant_id.get()


def tenant_id_para_columna() -> str:
    """Default ORM: copia el tenant del contexto al insertar."""
    return tenant_id_actual()


def del_tenant(modelo: Any) -> Any:
    """Filtro SQLAlchemy: filas del comercio actual."""
    return modelo.tenant_id == tenant_id_actual()


def es_del_tenant(entidad: Any | None) -> bool:
    """True si la entidad pertenece al comercio del contexto."""
    if entidad is None:
        return False
    return getattr(entidad, "tenant_id", None) == tenant_id_actual()


@contextmanager
def usando_tenant(tenant_id: str) -> Iterator[None]:
    """Fija el tenant (seed, tests, dependencia HTTP)."""
    token = _tenant_id.set(tenant_id)
    try:
        yield
    finally:
        _tenant_id.reset(token)


class ConTenant:
    """Mixin: tenant_id débil en tablas de negocio (sin FK entre módulos)."""

    tenant_id: Mapped[str] = mapped_column(
        String(36), index=True, default=tenant_id_para_columna
    )
