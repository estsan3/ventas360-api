"""DTOs del módulo reportería."""

from pydantic import BaseModel


class KpisResponse(BaseModel):
    """KPIs del dashboard comercial."""

    clientes_activos: int
    productos_activos: int
    ventas_mes: int
    monto_ventas_mes: float
    ticket_promedio: float
    moneda: str
