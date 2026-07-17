"""DTOs del módulo reportería."""

from pydantic import BaseModel


class ArticuloTopResponse(BaseModel):
    producto_id: str
    descripcion: str
    cantidad: int
    monto: float


class KpisResponse(BaseModel):
    """KPIs del dashboard comercial (datos reales)."""

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
