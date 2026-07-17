"""Utilidades de paginación compartidas (sin lógica de negocio)."""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginaParams(BaseModel):
    """Parámetros de listado paginado."""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)
    q: str | None = None


class PaginaResponse(BaseModel, Generic[T]):
    """Respuesta estándar de listados paginados."""

    items: list[T]
    total: int
    page: int
    page_size: int

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


def calcular_offset(page: int, page_size: int) -> int:
    return (max(page, 1) - 1) * page_size
