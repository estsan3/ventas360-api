"""Capa SERVICE del módulo reportería."""

from datetime import date, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.modulos.clientes.contrato import ClientesLocal, ContratoClientes
from app.modulos.cxc.bo import CxcBO
from app.modulos.cxc.dao import CxcDAO
from app.modulos.parametros.contrato import ContratoParametros, ParametrosLocal
from app.modulos.productos.contrato import ContratoProductos, ProductosLocal
from app.modulos.reporteria.schemas import (
    ArticuloStockDashResponse,
    ArticuloTopResponse,
    ComprobanteDashResponse,
    KpisResponse,
    PuntoSerieResponse,
    VencimientoDashResponse,
)
from app.modulos.ventas.contrato import ContratoVentas, VentasLocal

UMBRAL_STOCK_BAJO = 5
DIAS_VENCIDO = 30
_DIAS_CORTO = ("Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom")
_ETIQUETA_TIPO = {
    "factura": "FAC",
    "remito": "REM",
    "pedido": "PED",
}
_ETIQUETA_ESTADO = {
    "confirmado": "Confirmado",
    "entregado": "Entregado",
    "facturado": "Facturado",
    "borrador": "Borrador",
    "cancelado": "Cancelado",
    "vigente": "Vigente",
    "aceptado": "Aceptado",
    "convertido": "Convertido",
}


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
        self._cxc = CxcDAO(sesion)
        self._cxc_bo = CxcBO()

    async def obtener_kpis(self) -> KpisResponse:
        clientes_activos = await self._clientes.contar_activos()
        productos_activos = await self._productos.contar_activos()
        dia = await self._ventas.metricas_dia()
        mes = await self._ventas.metricas_mes()
        pendientes = await self._ventas.pendientes()
        top = await self._ventas.top_articulos(5)
        negocio = await self._parametros.obtener_negocio()
        bajo_stock, sin_stock = await self._productos.contar_bajo_stock(UMBRAL_STOCK_BAJO)
        reposicion = await self._productos.listar_bajo_stock(
            umbral=UMBRAL_STOCK_BAJO, limite=8
        )
        serie = await self._ventas.serie_semana()
        recientes = await self._ventas.listar_recientes(8)
        saldos = await self._cxc.saldos_agrupados()

        ids_nombres = {c.cliente_id for c in recientes}
        ids_nombres.update(fila[0] for fila in saldos)
        nombres = await self._clientes.nombres_por_ids(list(ids_nombres))

        saldo_cobrar = 0.0
        saldo_vencido = 0.0
        vencimientos: list[VencimientoDashResponse] = []
        hoy = date.today()
        limite_vencido = hoy - timedelta(days=DIAS_VENCIDO)
        for cliente_id, debe, haber, _ultimo, fecha_debe in saldos:
            saldo = self._cxc_bo.calcular_saldo(debe, haber)
            if saldo <= 0:
                continue
            saldo_cobrar += saldo
            fecha_debe_d = _a_fecha(fecha_debe)
            vencido = fecha_debe_d is not None and fecha_debe_d <= limite_vencido
            if vencido:
                saldo_vencido += saldo
            vencimientos.append(
                VencimientoDashResponse(
                    cliente=nombres.get(cliente_id, "Cliente"),
                    fecha=fecha_debe_d,
                    monto=round(saldo, 2),
                    vencido=vencido,
                )
            )
        vencimientos.sort(key=lambda v: (not v.vencido, v.fecha or hoy, -v.monto))
        vencimientos = vencimientos[:8]

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
            saldo_cobrar=round(saldo_cobrar, 2),
            saldo_vencido=round(saldo_vencido, 2),
            articulos_bajo_stock=bajo_stock,
            articulos_sin_stock=sin_stock,
            serie_semana=[
                PuntoSerieResponse(
                    fecha=p.fecha,
                    label="Hoy" if p.fecha == hoy else _DIAS_CORTO[p.fecha.weekday()],
                    monto=round(p.monto, 2),
                    cantidad=p.cantidad,
                    es_hoy=p.fecha == hoy,
                )
                for p in serie
            ],
            ultimos_comprobantes=[
                ComprobanteDashResponse(
                    id=c.id,
                    numero=_numero_comprobante(c.tipo, c.numero, c.id),
                    cliente=nombres.get(c.cliente_id, "Cliente"),
                    total=round(c.total, 2),
                    estado=_ETIQUETA_ESTADO.get(c.estado, c.estado.capitalize()),
                    tipo=c.tipo,
                )
                for c in recientes
            ],
            reposicion=[
                ArticuloStockDashResponse(
                    nombre=a.nombre,
                    detalle=a.sku,
                    stock=a.stock,
                )
                for a in reposicion
            ],
            vencimientos=vencimientos,
        )


def _numero_comprobante(tipo: str, numero: str | None, comprobante_id: str) -> str:
    if numero and numero.strip():
        return numero.strip()
    prefijo = _ETIQUETA_TIPO.get(tipo, tipo[:3].upper())
    return f"{prefijo} {comprobante_id[:8]}"


def _a_fecha(valor: object) -> date | None:
    if valor is None:
        return None
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    return None
