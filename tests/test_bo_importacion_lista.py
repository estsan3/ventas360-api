"""Tests del BO/parser de listas Excel de proveedores."""

from io import BytesIO

import pytest
from openpyxl import Workbook

from app.core.excepciones import ReglaDeNegocioViolada
from app.modulos.proveedores.bo import ProveedorBO
from app.modulos.proveedores.excel import parsear_lista_excel, parsear_numero


def _xlsx_bytes(filas: list[list]) -> bytes:
    wb = Workbook()
    ws = wb.active
    assert ws is not None
    for fila in filas:
        ws.append(fila)
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_parsear_numero_formato_ar() -> None:
    assert parsear_numero("61.900,00") == 61900.0
    assert parsear_numero(1480) == 1480.0


def test_validar_mapeo_requiere_codigo_y_costo() -> None:
    with pytest.raises(ReglaDeNegocioViolada, match="Código"):
        ProveedorBO().validar_mapeo(
            [{"columna": "A", "campo": "descripcion"}]
        )


def test_resolver_precio_margen() -> None:
    precio, actualizar = ProveedorBO().resolver_precio_venta(
        politica="margen_fijo", costo=100.0, precio_lista=None, margen_pct=30.0
    )
    assert actualizar is True
    assert precio == 130.0


def test_parsear_lista_excel_basica() -> None:
    contenido = _xlsx_bytes(
        [
            ["codigo", "desc", "costo"],
            ["H-4402", "Amoladora", "61.900,00"],
            ["H-1180", "Disco", 1480],
        ]
    )
    mapeo = [
        {"columna": "A", "campo": "codigo_producto"},
        {"columna": "B", "campo": "descripcion"},
        {"columna": "C", "campo": "precio_costo"},
    ]
    resultado = parsear_lista_excel(contenido, mapeo, fila_inicio=2)
    assert len(resultado.filas) == 2
    assert resultado.filas[0].sku == "H-4402"
    assert resultado.filas[0].costo == 61900.0
    assert resultado.filas[1].costo == 1480.0
    assert resultado.preview_cols[0].startswith("A")
