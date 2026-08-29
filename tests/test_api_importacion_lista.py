"""Integración: lista del proveedor no crea catálogo; el alta es explícita."""

from io import BytesIO

import pytest
from openpyxl import Workbook


def _xlsx(filas: list[list]) -> bytes:
    wb = Workbook()
    ws = wb.active
    assert ws is not None
    for fila in filas:
        ws.append(fila)
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


@pytest.mark.asyncio
async def test_importar_lista_no_crea_articulos(cliente, auth_headers) -> None:
    prov = await cliente.post(
        "/api/v1/proveedores",
        headers=auth_headers,
        json={
            "nombre": "Proveedor Lista SA",
            "cuit": "30711222334",
            "mapeo_excel": [
                {"columna": "A", "campo": "codigo_producto"},
                {"columna": "B", "campo": "descripcion"},
                {"columna": "C", "campo": "precio_costo"},
            ],
            "excel_fila_inicio": 2,
            "politica_precio_venta": "solo_costo",
        },
    )
    assert prov.status_code == 201, prov.text
    proveedor_id = prov.json()["id"]

    contenido = _xlsx(
        [
            ["sku", "nombre", "costo"],
            ["SKU-IMP-1", "Tornillo 8mm", 125.5],
            ["SKU-IMP-2", "Tuerca 8mm", 40],
        ]
    )
    imp = await cliente.post(
        f"/api/v1/proveedores/{proveedor_id}/listas/importar",
        headers=auth_headers,
        params={"dry_run": "false"},
        files={
            "archivo": (
                "lista.xlsx",
                contenido,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert imp.status_code == 200, imp.text
    body = imp.json()
    assert body["actualizados"] == 0
    assert body["sin_match"] == 2

    productos = await cliente.get(
        "/api/v1/productos",
        headers=auth_headers,
        params={"q": "SKU-IMP-1", "page_size": 10},
    )
    assert productos.status_code == 200
    assert productos.json()["items"] == []

    items = await cliente.get(
        f"/api/v1/proveedores/{proveedor_id}/listas/items",
        headers=auth_headers,
    )
    assert items.status_code == 200
    assert items.json()["total"] == 2
    tornillo = next(i for i in items.json()["items"] if i["codigo_proveedor"] == "SKU-IMP-1")
    assert tornillo["en_catalogo"] is False

    alta = await cliente.post(
        f"/api/v1/proveedores/{proveedor_id}/listas/items/{tornillo['id']}/alta",
        headers=auth_headers,
        json={"sku": "1005"},
    )
    assert alta.status_code == 200, alta.text
    assert alta.json()["en_catalogo"] is True

    catalogo = await cliente.get(
        "/api/v1/productos",
        headers=auth_headers,
        params={"q": "1005", "page_size": 10},
    )
    art = next(p for p in catalogo.json()["items"] if p["sku"] == "1005")
    assert art["costo"] == 125.5
    assert art["codigo_proveedor"] == "SKU-IMP-1"

    dep = await cliente.post(
        "/api/v1/stock/depositos",
        headers=auth_headers,
        json={"codigo": "DEP-T", "nombre": "Depósito test"},
    )
    assert dep.status_code == 201, dep.text

    compra = await cliente.post(
        "/api/v1/compras",
        headers=auth_headers,
        json={
            "proveedor_id": proveedor_id,
            "tipo": "remito_compra",
            "deposito_id": dep.json()["id"],
            "lineas": [{"producto_id": art["id"], "cantidad": 3}],
        },
    )
    assert compra.status_code == 201, compra.text
    assert compra.json()["lineas"][0]["precio_unitario"] == 125.5

    conf = await cliente.post(
        f"/api/v1/compras/{compra.json()['id']}/confirmar",
        headers=auth_headers,
    )
    assert conf.status_code == 200, conf.text
    assert conf.json()["estado"] == "confirmado"


@pytest.mark.asyncio
async def test_importar_actualiza_si_ya_existe_en_catalogo(cliente, auth_headers) -> None:
    prod = await cliente.post(
        "/api/v1/productos",
        headers=auth_headers,
        json={"sku": "H-4402", "nombre": "Amoladora", "precio": 200, "stock": 0, "costo": 50},
    )
    assert prod.status_code == 201, prod.text

    prov = await cliente.post(
        "/api/v1/proveedores",
        headers=auth_headers,
        json={
            "nombre": "Prov Match",
            "mapeo_excel": [
                {"columna": "A", "campo": "codigo_producto"},
                {"columna": "B", "campo": "descripcion"},
                {"columna": "C", "campo": "precio_costo"},
            ],
            "excel_fila_inicio": 2,
        },
    )
    proveedor_id = prov.json()["id"]
    contenido = _xlsx([["c", "n", "p"], ["H-4402", "Amoladora 750W", 80]])
    imp = await cliente.post(
        f"/api/v1/proveedores/{proveedor_id}/listas/importar",
        headers=auth_headers,
        params={"dry_run": "false"},
        files={
            "archivo": (
                "lista.xlsx",
                contenido,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert imp.json()["actualizados"] == 1
    assert imp.json()["sin_match"] == 0

    detalle = await cliente.get(
        f"/api/v1/productos/{prod.json()['id']}",
        headers=auth_headers,
    )
    assert detalle.json()["costo"] == 80
