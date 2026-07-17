"""Capa SERVICE del módulo reportería.

Reportería es un módulo de solo lectura que COMPONE datos de otros
módulos a través de sus contratos públicos. No tiene DAO ni BO propios.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.modulos.clientes.contrato import ClientesLocal, ContratoClientes
from app.modulos.parametros.contrato import ContratoParametros, ParametrosLocal
from app.modulos.productos.contrato import ContratoProductos, ProductosLocal
from app.modulos.reporteria.schemas import KpisResponse
from app.modulos.ventas.contrato import ContratoVentas, VentasLocal


class ReporteriaService:
    """Casos de uso de métricas y KPIs."""

    def __init__(
        self,
        sesion: AsyncSession,
        clientes: ContratoClientes | None = None,
        productos: ContratoProductos | None = None,
        ventas: ContratoVentas | None = None,
        parametros: ContratoParametros | None = None,
    ) -> None:
        self._clientes = clientes or ClientesLocal(sesion)
        self._productos = productos or ProductosLocal(sesion)
        self._ventas = ventas or VentasLocal(sesion)
        self._parametros = parametros or ParametrosLocal(sesion)

    async def obtener_kpis(self) -> KpisResponse:
        """Combina métricas de clientes, productos y ventas del mes."""
        clientes_activos = await self._clientes.contar_activos()
        productos_activos = await self._productos.contar_activos()
        metricas = await self._ventas.metricas_mes()
        negocio = await self._parametros.obtener_negocio()

        ticket = (
            round(metricas.monto / metricas.cantidad, 2)
            if metricas.cantidad > 0
            else 0.0
        )

        return KpisResponse(
            clientes_activos=clientes_activos,
            productos_activos=productos_activos,
            ventas_mes=metricas.cantidad,
            monto_ventas_mes=round(metricas.monto, 2),
            ticket_promedio=ticket,
            moneda=negocio.moneda,
        )
