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


class ContratoVentas(Protocol):
    """Interfaz que ventas garantiza al resto del sistema."""

    async def metricas_mes(self) -> MetricasMes: ...


class VentasLocal:
    """Implementación local del contrato (mismo proceso, misma base)."""

    def __init__(self, sesion: AsyncSession) -> None:
        self._dao = VentasDAO(sesion)

    async def metricas_mes(self) -> MetricasMes:
        from datetime import date

        hoy = date.today()
        cantidad, monto = await self._dao.metricas_mes(hoy.year, hoy.month)
        return MetricasMes(cantidad=cantidad, monto=monto)
