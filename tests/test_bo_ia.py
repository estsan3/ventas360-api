"""Tests de reglas de acciones del día."""

from app.modulos.ia.bo import PRIORIDAD_ALTA, construir_acciones, narrativa_mock
from app.modulos.ia.mostrador import mostrador_desde_texto_mock
from app.modulos.reporteria.schemas import KpisResponse, VencimientoDashResponse


def _kpis(**kwargs) -> KpisResponse:
    base = dict(
        clientes_activos=10,
        productos_activos=50,
        ventas_dia=3,
        monto_ventas_dia=120000.0,
        ventas_mes=40,
        monto_ventas_mes=1500000.0,
        ticket_promedio=30000.0,
        pedidos_pendientes=0,
        remitos_pendientes=0,
        remitos_por_facturar=0,
        moneda="ARS",
        top_articulos=[],
        saldo_cobrar=0.0,
        saldo_vencido=0.0,
        articulos_bajo_stock=0,
        articulos_sin_stock=0,
        serie_semana=[],
        ultimos_comprobantes=[],
        reposicion=[],
        vencimientos=[],
    )
    base.update(kwargs)
    return KpisResponse(**base)


def test_acciones_cobrar_vencido() -> None:
    kpis = _kpis(
        saldo_vencido=50000,
        vencimientos=[
            VencimientoDashResponse(cliente="A", fecha=None, monto=50000, vencido=True),
        ],
    )
    acciones = construir_acciones(kpis, remitos_compra_borrador=0)
    assert any(a.tipo == "cobrar_cxc" and a.prioridad == PRIORIDAD_ALTA for a in acciones)


def test_mostrador_mock_extrae_cantidad() -> None:
    extraido = mostrador_desde_texto_mock("2 mouse para García")
    assert extraido.lineas[0].cantidad >= 1


def test_narrativa_mock_incluye_ventas() -> None:
    txt = narrativa_mock(_kpis(ventas_dia=2, monto_ventas_dia=1000))
    assert "2 venta" in txt
