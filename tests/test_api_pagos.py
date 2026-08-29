"""Pago a proveedor: CxP haber + impacto en caja o cartera."""

from uuid import uuid4

import pytest


async def _proveedor(cliente, auth_headers) -> str:
    resp = await cliente.post(
        "/api/v1/proveedores",
        headers=auth_headers,
        json={"nombre": f"Prov Pago {uuid4().hex[:6]}"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_pago_efectivo_imputa_cxp(cliente, auth_headers) -> None:
    prov = await _proveedor(cliente, auth_headers)
    pago = await cliente.post(
        "/api/v1/pagos",
        headers=auth_headers,
        json={
            "proveedor_id": prov,
            "monto": 200,
            "medio": "efectivo",
            "destinatario": "Prov Pago",
        },
    )
    assert pago.status_code == 201, pago.text
    body = pago.json()
    assert body["medio"] == "efectivo"
    assert body["monto"] == 200

    saldos = await cliente.get("/api/v1/cxp/saldos", headers=auth_headers)
    assert saldos.status_code == 200
    fila = next(s for s in saldos.json() if s["proveedor_id"] == prov)
    assert fila["haber"] == 200
    assert fila["saldo"] == -200


@pytest.mark.asyncio
async def test_pago_con_cheque_de_cartera(cliente, auth_headers) -> None:
    prov = await _proveedor(cliente, auth_headers)
    valor = await cliente.post(
        "/api/v1/bancos/valores",
        headers=auth_headers,
        json={
            "tipo": "cheque_tercero",
            "monto": 150,
            "numero": "88001",
            "banco_emisor": "Nación",
            "librador": "Cliente X",
            "recibido_de": "Cliente X",
        },
    )
    assert valor.status_code == 201, valor.text
    valor_id = valor.json()["id"]

    pago = await cliente.post(
        "/api/v1/pagos",
        headers=auth_headers,
        json={
            "proveedor_id": prov,
            "monto": 150,
            "medio": "cheque",
            "cheque_id": valor_id,
            "destinatario": "Herramientas SA",
        },
    )
    assert pago.status_code == 201, pago.text
    assert pago.json()["lineas"][0]["cheque_id"] == valor_id

    cartera = await cliente.get("/api/v1/bancos/valores", headers=auth_headers)
    item = next(v for v in cartera.json() if v["id"] == valor_id)
    assert item["estado"] == "entregado"
    assert item["entregado_a"] == "Herramientas SA"


@pytest.mark.asyncio
async def test_pago_proveedor_inexistente(cliente, auth_headers) -> None:
    resp = await cliente.post(
        "/api/v1/pagos",
        headers=auth_headers,
        json={"proveedor_id": "no-existe", "monto": 10, "medio": "efectivo"},
    )
    assert resp.status_code == 422
