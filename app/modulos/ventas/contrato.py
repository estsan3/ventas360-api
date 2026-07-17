"""Contrato público del módulo ventas."""

from dataclasses import dataclass
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.modulos.ventas.dao import VentasDAO


@dataclass(frozen=True)
class MetricasPeriodo:
    """Métricas agregadas de un período."""

    cantidad: int
    monto: float


# Alias histórico usado por reportería previa.
MetricasMes = MetricasPeriodo


@dataclass(frozen=True)
class FacturaResumen:
    """Datos mínimos de una factura confirmada para cobranzas/cxc."""

    id: str
    cliente_id: str
    total: float
    estado: str


@dataclass(frozen=True)
class ArticuloTop:
    producto_id: str
    descripcion: str
    cantidad: int
    monto: float


@dataclass(frozen=True)
class PendientesVentas:
    pedidos_borrador: int
    remitos_borrador: int
    remitos_confirmados: int


class ContratoVentas(Protocol):
    """Interfaz que ventas garantiza al resto del sistema."""

    async def metricas_mes(self) -> MetricasPeriodo: ...

    async def metricas_dia(self) -> MetricasPeriodo: ...

    async def pendientes(self) -> PendientesVentas: ...

    async def top_articulos(self, limite: int = 5) -> list[ArticuloTop]: ...

    async def obtener_factura(self, factura_id: str) -> FacturaResumen | None: ...


class VentasLocal:
    """Implementación local del contrato (mismo proceso, misma base)."""

    def __init__(self, sesion: AsyncSession) -> None:
        self._dao = VentasDAO(sesion)

    async def metricas_mes(self) -> MetricasPeriodo:
        from datetime import date

        hoy = date.today()
        cantidad, monto = await self._dao.metricas_mes(hoy.year, hoy.month)
        return MetricasPeriodo(cantidad=cantidad, monto=monto)

    async def metricas_dia(self) -> MetricasPeriodo:
        from datetime import date

        cantidad, monto = await self._dao.metricas_dia(date.today())
        return MetricasPeriodo(cantidad=cantidad, monto=monto)

    async def pendientes(self) -> PendientesVentas:
        return PendientesVentas(
            pedidos_borrador=await self._dao.contar_pendientes("pedido", "borrador"),
            remitos_borrador=await self._dao.contar_pendientes("remito", "borrador"),
            remitos_confirmados=await self._dao.contar_pendientes(
                "remito", "confirmado"
            ),
        )

    async def top_articulos(self, limite: int = 5) -> list[ArticuloTop]:
        filas = await self._dao.top_articulos(limite)
        return [
            ArticuloTop(
                producto_id=pid,
                descripcion=desc or pid,
                cantidad=cant,
                monto=monto,
            )
            for pid, desc, cant, monto in filas
        ]

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
