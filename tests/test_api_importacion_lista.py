"""Integración: importar lista Excel → artículos + remito con costo."""

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
async def test_importar_lista_y_remito_usa_costo(cliente, auth_headers) -> None:
    # Depósito
    dep = await cliente.post(
        "/api/v1/stock/depositos",
        headers=auth_headers,
        json={"codigo": "DEP-T", "nombre": "Depósito test"},
    )
    assert dep.status_code == 201, dep.text
    deposito_id = dep.json()["id"]

    # Proveedor
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
    assert body["nuevos"] == 2
    assert body["actualizados"] == 0

    productos = await cliente.get(
        "/api/v1/productos",
        headers=auth_headers,
        params={"q": "SKU-IMP-1", "page_size": 10},
    )
    assert productos.status_code == 200
    art = next(p for p in productos.json()["items"] if p["sku"] == "SKU-IMP-1")
    assert art["costo"] == 125.5

    compra = await cliente.post(
        "/api/v1/compras",
        headers=auth_headers,
        json={
            "proveedor_id": proveedor_id,
            "tipo": "remito_compra",
            "deposito_id": deposito_id,
            "lineas": [{"producto_id": art["id"], "cantidad": 3}],
        },
    )
    assert compra.status_code == 201, compra.text
    creada = compra.json()
    assert creada["lineas"][0]["precio_unitario"] == 125.5

    conf = await cliente.post(
        f"/api/v1/compras/{creada['id']}/confirmar",
        headers=auth_headers,
    )
    assert conf.status_code == 200, conf.text
    assert conf.json()["estado"] == "confirmado"
