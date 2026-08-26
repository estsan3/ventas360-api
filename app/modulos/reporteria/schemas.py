"""DTOs del módulo reportería."""

from datetime import date

from pydantic import BaseModel


class ArticuloTopResponse(BaseModel):
    producto_id: str
    descripcion: str
    cantidad: int
    monto: float


class PuntoSerieResponse(BaseModel):
    fecha: date
    label: str
    monto: float
    cantidad: int
    es_hoy: bool


class ComprobanteDashResponse(BaseModel):
    id: str
    numero: str
    cliente: str
    total: float
    estado: str
    tipo: str


class ArticuloStockDashResponse(BaseModel):
    nombre: str
    detalle: str
    stock: int


class VencimientoDashResponse(BaseModel):
    cliente: str
    fecha: date | None
    monto: float
    vencido: bool


class KpisResponse(BaseModel):
    """KPIs del dashboard comercial (datos reales del comercio)."""

    clientes_activos: int
    productos_activos: int
    ventas_dia: int
    monto_ventas_dia: float
    ventas_mes: int
    monto_ventas_mes: float
    ticket_promedio: float
    pedidos_pendientes: int
    remitos_pendientes: int
    remitos_por_facturar: int
    moneda: str
    top_articulos: list[ArticuloTopResponse]
    saldo_cobrar: float
    saldo_vencido: float
    articulos_bajo_stock: int
    articulos_sin_stock: int
    serie_semana: list[PuntoSerieResponse]
    ultimos_comprobantes: list[ComprobanteDashResponse]
    reposicion: list[ArticuloStockDashResponse]
    vencimientos: list[VencimientoDashResponse]
