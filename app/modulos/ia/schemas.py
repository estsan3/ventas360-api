"""DTOs del módulo IA."""

from pydantic import BaseModel, Field


class LineaMostradorInterpretadaResponse(BaseModel):
    producto_id: str | None = None
    descripcion: str
    cantidad: int
    precio_unitario: float | None = None
    producto_nombre: str | None = None
    producto_sku: str | None = None
    match_tipo: str | None = None


class InterpretarMostradorRequest(BaseModel):
    texto: str = Field(min_length=2, max_length=500)
    deposito_id: str | None = None


class InterpretarMostradorResponse(BaseModel):
    intencion: str = "armar_venta"
    tipo: str = "remito"
    cliente_id: str | None = None
    cliente_nombre: str | None = None
    deposito_id: str | None = None
    lineas: list[LineaMostradorInterpretadaResponse]
    confianza: float
    advertencias: list[str] = Field(default_factory=list)
    preguntas: list[str] = Field(default_factory=list)
    modo_parser: str


class AccionDiaResponse(BaseModel):
    id: str
    tipo: str
    prioridad: str
    titulo: str
    detalle: str
    cantidad: int
    monto: float | None = None
    ruta_web: str


class AccionesDiaResponse(BaseModel):
    acciones: list[AccionDiaResponse]
    generado_en: str


class ResumenDiaMetricasResponse(BaseModel):
    ventas_dia: int
    monto_ventas_dia: float
    pedidos_pendientes: int
    remitos_por_facturar: int
    saldo_cobrar: float
    saldo_vencido: float
    articulos_bajo_stock: int
    articulos_sin_stock: int
    moneda: str


class ResumenDiaResponse(BaseModel):
    metricas: ResumenDiaMetricasResponse
    narrativa: str | None = None
    modo_narrativa: str | None = None
    acciones_destacadas: list[str] = Field(default_factory=list)
