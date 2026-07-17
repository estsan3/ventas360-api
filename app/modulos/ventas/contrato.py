"""Contrato público del módulo ventas."""

from dataclasses import dataclass
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.modulos.ventas.dao import VentasDAO


@dataclass(frozen=True)
class MetricasMes:
    """Métricas agregadas de ventas del mes."""

    cantidad: int
    monto: float


@dataclass(frozen=True)
class FacturaResumen:
    """Datos mínimos de una factura confirmada para cobranzas/cxc."""

    id: str
    cliente_id: str
    total: float
    estado: str


class ContratoVentas(Protocol):
    """Interfaz que ventas garantiza al resto del sistema."""

    async def metricas_mes(self) -> MetricasMes: ...

    async def obtener_factura(self, factura_id: str) -> FacturaResumen | None: ...


class VentasLocal:
    """Implementación local del contrato (mismo proceso, misma base)."""

    def __init__(self, sesion: AsyncSession) -> None:
        self._dao = VentasDAO(sesion)

    async def metricas_mes(self) -> MetricasMes:
        from datetime import date

        hoy = date.today()
        cantidad, monto = await self._dao.metricas_mes(hoy.year, hoy.month)
        return MetricasMes(cantidad=cantidad, monto=monto)

    async def obtener_factura(self, factura_id: str) -> FacturaResumen | None:
        comprobante = await self._dao.buscar_por_id(factura_id)
        if (
            comprobante is None
            or comprobante.tipo != "factura"
            or comprobante.estado != "confirmado"
        ):
            return None
        return FacturaResumen(
            id=comprobante.id,
            cliente_id=comprobante.cliente_id,
            total=comprobante.total,
            estado=comprobante.estado,
        )
