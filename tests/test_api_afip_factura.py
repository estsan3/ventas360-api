"""Integración B4: factura fiscal con adapter simulado (CAE)."""

import pytest


async def _habilitar_arca(cliente, auth_headers) -> None:
    resp = await cliente.put(
        "/api/v1/parametros/afip",
        headers=auth_headers,
        json={
            "habilitada": True,
            "cuit": "30712345682",
            "razon_social": "Comercio Test",
            "condicion_iva": "responsable_inscripto",
            "punto_venta": 1,
            "domicilio": "Calle Falsa 123",
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["habilitada"] is True
    assert body["proveedor"] == "simulado"


async def _catalogo_factura(cliente, auth_headers) -> dict[str, str]:
    cli = await cliente.post(
        "/api/v1/clientes",
        headers=auth_headers,
        json={
            "nombre": "Cliente CF",
            "email": "cf-arca@demo.com",
            "telefono": "1",
            "condicion_iva": "consumidor_final",
        },
    )
    assert cli.status_code == 201, cli.text
    prod = await cliente.post(
        "/api/v1/productos",
        headers=auth_headers,
        json={
            "sku": "ARCA-SKU-1",
            "nombre": "Artículo fiscal",
            "precio": 100.0,
            "costo": 50.0,
            "stock": 10,
        },
    )
    assert prod.status_code == 201, prod.text
    return {"cliente_id": cli.json()["id"], "articulo_id": prod.json()["id"]}


@pytest.mark.asyncio
async def test_confirmar_factura_asigna_cae_simulado(cliente, auth_headers) -> None:
    await _habilitar_arca(cliente, auth_headers)
    ids = await _catalogo_factura(cliente, auth_headers)

    crear = await cliente.post(
        "/api/v1/ventas/pedidos",
        headers=auth_headers,
        json={
            "tipo": "factura",
            "cliente_id": ids["cliente_id"],
            "lineas": [{"producto_id": ids["articulo_id"], "cantidad": 1}],
        },
    )
    assert crear.status_code == 201, crear.text
    factura = crear.json()
    assert factura["letra"] == "B"
    assert factura["cbte_tipo"] == 6
    assert factura["cae"] is None

    confirmar = await cliente.patch(
        f"/api/v1/ventas/pedidos/{factura['id']}/estado",
        headers=auth_headers,
        json={"estado": "confirmado"},
    )
    assert confirmar.status_code == 200, confirmar.text
    body = confirmar.json()
    assert body["estado"] == "confirmado"
    assert body["cae"]
    assert len(body["cae"]) == 14
    assert body["cae_vencimiento"]
    assert body["numero"].startswith("B-00001-")
    assert body["qr_url"].startswith("https://www.afip.gob.ar/fe/qr/?p=")


@pytest.mark.asyncio
async def test_factura_a_sin_cuit_falla(cliente, auth_headers) -> None:
    await _habilitar_arca(cliente, auth_headers)
    cli = await cliente.post(
        "/api/v1/clientes",
        headers=auth_headers,
        json={
            "nombre": "RI sin CUIT",
            "email": "ri-sin-cuit@demo.com",
            "condicion_iva": "responsable_inscripto",
        },
    )
    assert cli.status_code == 201, cli.text
    prod = await cliente.post(
        "/api/v1/productos",
        headers=auth_headers,
        json={
            "sku": "ARCA-SKU-2",
            "nombre": "Artículo A",
            "precio": 100.0,
            "costo": 50.0,
            "stock": 5,
        },
    )
    assert prod.status_code == 201, prod.text
    crear = await cliente.post(
        "/api/v1/ventas/pedidos",
        headers=auth_headers,
        json={
            "tipo": "factura",
            "cliente_id": cli.json()["id"],
            "lineas": [{"producto_id": prod.json()["id"], "cantidad": 1}],
        },
    )
    assert crear.status_code == 201, crear.text
    confirmar = await cliente.patch(
        f"/api/v1/ventas/pedidos/{crear.json()['id']}/estado",
        headers=auth_headers,
        json={"estado": "confirmado"},
    )
    assert confirmar.status_code == 422
    assert "Factura A" in confirmar.json()["error"]["mensaje"]


@pytest.mark.asyncio
async def test_habilitar_arca_sin_cuit_falla(cliente, auth_headers) -> None:
    resp = await cliente.put(
        "/api/v1/parametros/afip",
        headers=auth_headers,
        json={
            "habilitada": True,
            "cuit": "",
            "razon_social": "X",
            "condicion_iva": "responsable_inscripto",
            "punto_venta": 1,
            "domicilio": "",
        },
    )
    assert resp.status_code == 422
