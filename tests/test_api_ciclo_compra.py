"""Ciclo pedido de compra → remito parcial → factura sin duplicar stock."""

import pytest


async def _setup(cliente, auth_headers) -> dict[str, str]:
    dep = await cliente.post(
        "/api/v1/stock/depositos",
        headers=auth_headers,
        json={"codigo": "DEP-OC", "nombre": "Central"},
    )
    prod = await cliente.post(
        "/api/v1/productos",
        headers=auth_headers,
        json={
            "sku": "AMO-1005",
            "nombre": "Amoladora",
            "precio": 150,
            "stock": 0,
            "costo": 100,
        },
    )
    prov = await cliente.post(
        "/api/v1/proveedores",
        headers=auth_headers,
        json={"nombre": "Herramientas SA"},
    )
    return {
        "deposito_id": dep.json()["id"],
        "producto_id": prod.json()["id"],
        "proveedor_id": prov.json()["id"],
    }


@pytest.mark.asyncio
async def test_ciclo_pedido_remito_parcial_factura(cliente, auth_headers) -> None:
    ids = await _setup(cliente, auth_headers)

    pedido = await cliente.post(
        "/api/v1/compras",
        headers=auth_headers,
        json={
            "proveedor_id": ids["proveedor_id"],
            "tipo": "pedido_compra",
            "deposito_id": ids["deposito_id"],
            "lineas": [{"producto_id": ids["producto_id"], "cantidad": 10}],
        },
    )
    assert pedido.status_code == 201, pedido.text
    pedido_id = pedido.json()["id"]
    assert pedido.json()["estado"] == "borrador"

    emitir = await cliente.post(
        f"/api/v1/compras/{pedido_id}/emitir",
        headers=auth_headers,
    )
    assert emitir.json()["estado"] == "emitido"

    # Confirmar el pedido no ingresa stock.
    mal = await cliente.post(
        f"/api/v1/compras/{pedido_id}/confirmar",
        headers=auth_headers,
    )
    assert mal.status_code == 422

    remito = await cliente.post(
        "/api/v1/compras",
        headers=auth_headers,
        json={
            "proveedor_id": ids["proveedor_id"],
            "tipo": "remito_compra",
            "deposito_id": ids["deposito_id"],
            "origen_id": pedido_id,
            "lineas": [{"producto_id": ids["producto_id"], "cantidad": 4}],
        },
    )
    remito_id = remito.json()["id"]
    conf = await cliente.post(
        f"/api/v1/compras/{remito_id}/confirmar",
        headers=auth_headers,
    )
    assert conf.status_code == 200, conf.text

    pedido_act = await cliente.get(
        f"/api/v1/compras/{pedido_id}",
        headers=auth_headers,
    )
    assert pedido_act.json()["estado"] == "parcial"
    assert pedido_act.json()["cantidad_pedida"] == 10
    assert pedido_act.json()["cantidad_recibida"] == 4

    prod = await cliente.get(
        f"/api/v1/productos/{ids['producto_id']}",
        headers=auth_headers,
    )
    assert prod.json()["stock"] == 4

    factura = await cliente.post(
        f"/api/v1/compras/{remito_id}/facturar",
        headers=auth_headers,
    )
    assert factura.status_code == 200, factura.text
    assert factura.json()["tipo"] == "factura_compra"
    assert factura.json()["estado"] == "confirmado"

    prod2 = await cliente.get(
        f"/api/v1/productos/{ids['producto_id']}",
        headers=auth_headers,
    )
    assert prod2.json()["stock"] == 4
