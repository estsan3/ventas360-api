"""Integración: parsear remito desde foto (mock) y crear compra."""

import pytest


def _png_minimo() -> bytes:
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
        b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01"
        b"\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )


async def _crear_proveedor_deposito(cliente, auth_headers, sufijo: str) -> tuple[str, str]:
    prov = await cliente.post(
        "/api/v1/proveedores",
        headers=auth_headers,
        json={"nombre": f"Prov Remito {sufijo}", "cuit": "30711222334"},
    )
    assert prov.status_code == 201, prov.text
    dep = await cliente.post(
        "/api/v1/stock/depositos",
        headers=auth_headers,
        json={"codigo": f"D{sufijo}", "nombre": f"Dep {sufijo}"},
    )
    assert dep.status_code == 201, dep.text
    return prov.json()["id"], dep.json()["id"]


async def _crear_productos_mock(cliente, auth_headers) -> None:
    for sku, nombre, barras in (
        ("MS-010", "Mouse inalámbrico", "7790001000002"),
        ("TK-200", "Teclado mecánico", "7790001000003"),
    ):
        resp = await cliente.post(
            "/api/v1/productos",
            headers=auth_headers,
            json={
                "sku": sku,
                "nombre": nombre,
                "codigo_barras": barras,
                "costo": 9000 if sku == "MS-010" else 22000,
                "precio": 18500 if sku == "MS-010" else 42000,
            },
        )
        assert resp.status_code == 201, resp.text


@pytest.mark.asyncio
async def test_parsear_remito_mock_y_crear_compra(cliente, auth_headers) -> None:
    proveedor_id, deposito_id = await _crear_proveedor_deposito(cliente, auth_headers, "001")
    await _crear_productos_mock(cliente, auth_headers)

    parsed = await cliente.post(
        "/api/v1/compras/remitos/parsear",
        headers=auth_headers,
        data={"proveedor_id": proveedor_id, "deposito_id": deposito_id},
        files={"archivo": ("remito.png", _png_minimo(), "image/png")},
    )
    assert parsed.status_code == 200, parsed.text
    body = parsed.json()
    assert body["modo_parser"] == "mock"
    assert body["sin_match"] == 0
    assert len(body["lineas"]) == 2

    compra = await cliente.post(
        "/api/v1/compras",
        headers=auth_headers,
        json={
            "proveedor_id": proveedor_id,
            "tipo": "remito_compra",
            "deposito_id": deposito_id,
            "lineas": [
                {
                    "producto_id": linea["producto_id"],
                    "cantidad": linea["cantidad"],
                    **(
                        {"precio_unitario": linea["precio_unitario"]}
                        if linea.get("precio_unitario") is not None
                        else {}
                    ),
                }
                for linea in body["lineas"]
                if linea["producto_id"]
            ],
        },
    )
    assert compra.status_code == 201, compra.text
    compra_id = compra.json()["id"]

    conf = await cliente.post(
        f"/api/v1/compras/{compra_id}/confirmar",
        headers=auth_headers,
    )
    assert conf.status_code == 200, conf.text
    assert conf.json()["estado"] == "confirmado"


@pytest.mark.asyncio
async def test_parsear_remito_rechaza_no_imagen(cliente, auth_headers) -> None:
    proveedor_id, _ = await _crear_proveedor_deposito(cliente, auth_headers, "002")
    resp = await cliente.post(
        "/api/v1/compras/remitos/parsear",
        headers=auth_headers,
        data={"proveedor_id": proveedor_id},
        files={"archivo": ("lista.txt", b"hola", "text/plain")},
    )
    assert resp.status_code == 422 or resp.status_code == 400
