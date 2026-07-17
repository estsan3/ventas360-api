"""Integración A5: remito → confirma (stock) → factura."""

import pytest


async def _setup_catalogo(cliente, auth_headers) -> dict[str, str]:
    cli = await cliente.post(
        "/api/v1/clientes",
        headers=auth_headers,
        json={
            "nombre": "Cliente Remito",
            "email": "remito@demo.com",
            "telefono": "1",
        },
    )
    assert cli.status_code == 201, cli.text
    cliente_id = cli.json()["id"]

    prod = await cliente.post(
        "/api/v1/productos",
        headers=auth_headers,
        json={
            "sku": "REM-SKU-1",
            "nombre": "Artículo remito",
            "precio": 100.0,
            "costo": 50.0,
            "stock": 10,
        },
    )
    assert prod.status_code == 201, prod.text
    articulo_id = prod.json()["id"]

    dep = await cliente.post(
        "/api/v1/stock/depositos",
        headers=auth_headers,
        json={"codigo": "R1", "nombre": "Dep remito"},
    )
    assert dep.status_code == 201, dep.text
    deposito_id = dep.json()["id"]

    ajuste = await cliente.post(
        "/api/v1/stock/ajustes",
        headers=auth_headers,
        json={
            "articulo_id": articulo_id,
            "deposito_id": deposito_id,
            "cantidad": 10,
            "referencia": "carga inicial test",
        },
    )
    assert ajuste.status_code == 200, ajuste.text

    return {
        "cliente_id": cliente_id,
        "articulo_id": articulo_id,
        "deposito_id": deposito_id,
    }


@pytest.mark.asyncio
async def test_flujo_remito_factura_y_stock(cliente, auth_headers) -> None:
    ids = await _setup_catalogo(cliente, auth_headers)

    crear = await cliente.post(
        "/api/v1/ventas/pedidos",
        headers=auth_headers,
        json={
            "tipo": "remito",
            "cliente_id": ids["cliente_id"],
            "deposito_id": ids["deposito_id"],
            "lineas": [{"producto_id": ids["articulo_id"], "cantidad": 3}],
        },
    )
    assert crear.status_code == 201, crear.text
    remito = crear.json()
    assert remito["tipo"] == "remito"
    assert remito["estado"] == "borrador"
    assert remito["neto"] == 300.0
    assert remito["iva"] == 63.0
    assert remito["total"] == 363.0

    confirmar = await cliente.post(
        f"/api/v1/ventas/pedidos/{remito['id']}/confirmar-remito",
        headers=auth_headers,
    )
    assert confirmar.status_code == 200, confirmar.text
    assert confirmar.json()["estado"] == "confirmado"

    saldos = await cliente.get(
        f"/api/v1/stock/articulos/{ids['articulo_id']}/saldos",
        headers=auth_headers,
    )
    assert saldos.status_code == 200
    saldo = next(s for s in saldos.json() if s["deposito_id"] == ids["deposito_id"])
    assert saldo["cantidad"] == 7

    factura = await cliente.post(
        f"/api/v1/ventas/pedidos/{remito['id']}/facturar",
        headers=auth_headers,
    )
    assert factura.status_code == 200, factura.text
    body = factura.json()
    assert body["tipo"] == "factura"
    assert body["estado"] == "confirmado"
    assert body["origen_id"] == remito["id"]
    assert body["total"] == 363.0

    remito_final = await cliente.get(
        f"/api/v1/ventas/pedidos/{remito['id']}",
        headers=auth_headers,
    )
    assert remito_final.json()["estado"] == "facturado"
