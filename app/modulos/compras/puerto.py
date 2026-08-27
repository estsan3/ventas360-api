"""Puerto para parseo de remitos con visión (LLM externo)."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class LineaRemitoExtraida:
    """Línea cruda extraída de una imagen de remito."""

    descripcion: str
    cantidad: int
    sku: str | None = None
    codigo_barras: str | None = None
    precio_unitario: float | None = None
    unidad: str | None = None


@dataclass(frozen=True)
class RemitoExtraido:
    """Datos estructurados leídos de un remito."""

    numero: str | None
    fecha: str | None
    proveedor_texto: str | None
    lineas: list[LineaRemitoExtraida]
    confianza: float
    notas: list[str]


class PuertoParserRemitoVision(Protocol):
    """Contrato del adaptador de visión (Anthropic, mock, etc.)."""

    async def parsear(self, contenido: bytes, media_type: str) -> RemitoExtraido: ...
