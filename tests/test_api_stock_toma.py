"""Cierre de toma de inventario: ajusta saldos a las cantidades contadas."""

from uuid import uuid4

import pytest


async def _setup(cliente, auth_headers) -> dict[str, str]:
    sufijo = uuid4().hex[:8]
    prod = await cliente.post(
        "/api/v1/productos",
        headers=auth_headers,
        json={
            "sku": f"TOMA-{sufijo}",
            "nombre": "Gaseosa 2.25",
            "precio": 2000.0,
            "costo": 1200.0,
            "stock": 0,
        },
    )
    assert prod.status_code == 201, prod.text
    dep = await cliente.post(
        "/api/v1/stock/depositos",
        headers=auth_headers,
        json={"codigo": f"T{sufijo[:6].upper()}", "nombre": "Depósito toma"},
    )
    assert dep.status_code == 201, dep.text
    ajuste = await cliente.post(
        "/api/v1/stock/ajustes",
        headers=auth_headers,
        json={
            "articulo_id": prod.json()["id"],
            "deposito_id": dep.json()["id"],
            "cantidad": 10,
            "referencia": "carga inicial",
        },
    )
    assert ajuste.status_code == 200, ajuste.text
    return {
        "articulo_id": prod.json()["id"],
        "deposito_id": dep.json()["id"],
    }


@pytest.mark.asyncio
async def test_cerrar_toma_ajusta_saldo_y_catalogo(cliente, auth_headers) -> None:
    ids = await _setup(cliente, auth_headers)

    cierre = await cliente.post(
        "/api/v1/stock/tomas",
        headers=auth_headers,
        json={
            "deposito_id": ids["deposito_id"],
            "conteos": [{"articulo_id": ids["articulo_id"], "cantidad": 7}],
        },
    )
    assert cierre.status_code == 200, cierre.text
    body = cierre.json()
    assert body["ajustados"] == 1
    assert body["sin_cambio"] == 0
    assert body["ajustes"][0]["anterior"] == 10
    assert body["ajustes"][0]["nuevo"] == 7
    assert body["ajustes"][0]["delta"] == -3

    inv = await cliente.get(
        f"/api/v1/stock/depositos/{ids['deposito_id']}/inventario",
        headers=auth_headers,
    )
    assert inv.status_code == 200
    fila = next(i for i in inv.json() if i["articulo_id"] == ids["articulo_id"])
    assert fila["cantidad"] == 7

    prod = await cliente.get(
        f"/api/v1/productos/{ids['articulo_id']}",
        headers=auth_headers,
    )
    assert prod.status_code == 200
    assert prod.json()["stock"] == 7


@pytest.mark.asyncio
async def test_cerrar_toma_sin_diferencia_no_ajusta(cliente, auth_headers) -> None:
    ids = await _setup(cliente, auth_headers)
    cierre = await cliente.post(
        "/api/v1/stock/tomas",
        headers=auth_headers,
        json={
            "deposito_id": ids["deposito_id"],
            "conteos": [{"articulo_id": ids["articulo_id"], "cantidad": 10}],
        },
    )
    assert cierre.status_code == 200, cierre.text
    assert cierre.json()["ajustados"] == 0
    assert cierre.json()["sin_cambio"] == 1


@pytest.mark.asyncio
async def test_cerrar_toma_no_toca_articulos_sin_contar(cliente, auth_headers) -> None:
    ids = await _setup(cliente, auth_headers)
    otro = await cliente.post(
        "/api/v1/productos",
        headers=auth_headers,
        json={
            "sku": f"TOMA-B-{uuid4().hex[:8]}",
            "nombre": "Agua 2L",
            "precio": 800.0,
            "costo": 400.0,
            "stock": 0,
        },
    )
    assert otro.status_code == 201, otro.text
    carga = await cliente.post(
        "/api/v1/stock/ajustes",
        headers=auth_headers,
        json={
            "articulo_id": otro.json()["id"],
            "deposito_id": ids["deposito_id"],
            "cantidad": 4,
            "referencia": "carga inicial",
        },
    )
    assert carga.status_code == 200, carga.text

    cierre = await cliente.post(
        "/api/v1/stock/tomas",
        headers=auth_headers,
        json={
            "deposito_id": ids["deposito_id"],
            "conteos": [{"articulo_id": ids["articulo_id"], "cantidad": 7}],
        },
    )
    assert cierre.status_code == 200, cierre.text

    inv = await cliente.get(
        f"/api/v1/stock/depositos/{ids['deposito_id']}/inventario",
        headers=auth_headers,
    )
    assert inv.status_code == 200
    por_id = {i["articulo_id"]: i["cantidad"] for i in inv.json()}
    assert por_id[ids["articulo_id"]] == 7
    assert por_id[otro.json()["id"]] == 4
