"""Tests de lógica pura de parseo y matching de remitos."""

from app.modulos.compras.puerto import LineaRemitoExtraida, RemitoExtraido
from app.modulos.compras.remito_vision import matchear_remito, remito_desde_json
from app.modulos.productos.contrato import ProductoResumen


def _prod(**kwargs) -> ProductoResumen:
    base = dict(
        id="p1",
        sku="MS-010",
        nombre="Mouse inalámbrico",
        precio=18500.0,
        costo=9000.0,
        stock=10,
        activo=True,
    )
    base.update(kwargs)
    return ProductoResumen(**base)


def test_remito_desde_json_lineas() -> None:
    data = {
        "numero": "R-001",
        "fecha": "2026-08-26",
        "lineas": [
            {"descripcion": "Mouse", "cantidad": 3, "sku": "MS-010"},
        ],
        "confianza": 0.9,
    }
    extraido = remito_desde_json(data)
    assert extraido.numero == "R-001"
    assert len(extraido.lineas) == 1
    assert extraido.lineas[0].cantidad == 3


def test_matchear_por_sku() -> None:
    mouse = _prod()
    extraido = RemitoExtraido(
        numero=None,
        fecha=None,
        proveedor_texto=None,
        confianza=0.8,
        notas=[],
        lineas=[
            LineaRemitoExtraida(descripcion="Mouse", cantidad=2, sku="MS-010"),
        ],
    )
    result = matchear_remito(
        extraido,
        por_codigo_barras={},
        por_sku={"MS-010": mouse},
        candidatos_nombre=[mouse],
    )
    assert result.sin_match == 0
    assert result.lineas[0].producto_id == "p1"
    assert result.lineas[0].match_tipo == "sku"


def test_matchear_sin_match() -> None:
    extraido = RemitoExtraido(
        numero=None,
        fecha=None,
        proveedor_texto=None,
        confianza=0.5,
        notas=[],
        lineas=[
            LineaRemitoExtraida(descripcion="Artículo desconocido XYZ", cantidad=1),
        ],
    )
    result = matchear_remito(
        extraido,
        por_codigo_barras={},
        por_sku={},
        candidatos_nombre=[],
    )
    assert result.sin_match == 1
    assert result.lineas[0].producto_id is None
