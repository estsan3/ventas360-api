"""Capa SERVICE del módulo reportería."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.modulos.clientes.contrato import ClientesLocal, ContratoClientes
from app.modulos.parametros.contrato import ContratoParametros, ParametrosLocal
from app.modulos.productos.contrato import ContratoProductos, ProductosLocal
from app.modulos.reporteria.schemas import ArticuloTopResponse, KpisResponse
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
        clientes_activos = await self._clientes.contar_activos()
        productos_activos = await self._productos.contar_activos()
        dia = await self._ventas.metricas_dia()
        mes = await self._ventas.metricas_mes()
        pendientes = await self._ventas.pendientes()
        top = await self._ventas.top_articulos(5)
        negocio = await self._parametros.obtener_negocio()

        ticket = round(mes.monto / mes.cantidad, 2) if mes.cantidad > 0 else 0.0

        return KpisResponse(
            clientes_activos=clientes_activos,
            productos_activos=productos_activos,
            ventas_dia=dia.cantidad,
            monto_ventas_dia=round(dia.monto, 2),
            ventas_mes=mes.cantidad,
            monto_ventas_mes=round(mes.monto, 2),
            ticket_promedio=ticket,
            pedidos_pendientes=pendientes.pedidos_borrador,
            remitos_pendientes=pendientes.remitos_borrador,
            remitos_por_facturar=pendientes.remitos_confirmados,
            moneda=negocio.moneda,
            top_articulos=[
                ArticuloTopResponse(
                    producto_id=a.producto_id,
                    descripcion=a.descripcion,
                    cantidad=a.cantidad,
                    monto=round(a.monto, 2),
                )
                for a in top
            ],
        )
