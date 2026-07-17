"""Integración A6–A7: remito → CxC → factura sin duplicar → recibo reduce saldo."""

import pytest


async def _setup(cliente, auth_headers) -> dict[str, str]:
    cli = await cliente.post(
        "/api/v1/clientes",
        headers=auth_headers,
        json={"nombre": "CxC Demo", "email": "cxc@demo.com", "telefono": "1"},
    )
    assert cli.status_code == 201, cli.text
    cliente_id = cli.json()["id"]

    prod = await cliente.post(
        "/api/v1/productos",
        headers=auth_headers,
        json={
            "sku": "CXC-1",
            "nombre": "Art CxC",
            "precio": 100.0,
            "costo": 40.0,
            "stock": 20,
        },
    )
    assert prod.status_code == 201, prod.text
    articulo_id = prod.json()["id"]

    dep = await cliente.post(
        "/api/v1/stock/depositos",
        headers=auth_headers,
        json={"codigo": "CXC-D", "nombre": "Dep CxC"},
    )
    assert dep.status_code == 201, dep.text
    deposito_id = dep.json()["id"]

    await cliente.post(
        "/api/v1/stock/ajustes",
        headers=auth_headers,
        json={
            "articulo_id": articulo_id,
            "deposito_id": deposito_id,
            "cantidad": 20,
        },
    )

    remito = await cliente.post(
        "/api/v1/ventas/pedidos",
        headers=auth_headers,
        json={
            "tipo": "remito",
            "cliente_id": cliente_id,
            "deposito_id": deposito_id,
            "lineas": [{"producto_id": articulo_id, "cantidad": 2}],
        },
    )
    assert remito.status_code == 201, remito.text
    remito_id = remito.json()["id"]
    # neto 200 + IVA 21% = 242
    assert remito.json()["total"] == 242.0

    conf = await cliente.post(
        f"/api/v1/ventas/pedidos/{remito_id}/confirmar-remito",
        headers=auth_headers,
    )
    assert conf.status_code == 200, conf.text

    saldo_post_remito = await cliente.get(
        f"/api/v1/cxc/clientes/{cliente_id}/saldo",
        headers=auth_headers,
    )
    assert saldo_post_remito.status_code == 200, saldo_post_remito.text
    assert saldo_post_remito.json()["saldo"] == 242.0

    factura = await cliente.post(
        f"/api/v1/ventas/pedidos/{remito_id}/facturar",
        headers=auth_headers,
    )
    assert factura.status_code == 200, factura.text
    return {
        "cliente_id": cliente_id,
        "remito_id": remito_id,
        "factura_id": factura.json()["id"],
        "total": str(factura.json()["total"]),
    }


@pytest.mark.asyncio
async def test_remito_imputa_cxc_factura_no_duplica_y_recibo_cancela(
    cliente, auth_headers
) -> None:
    ids = await _setup(cliente, auth_headers)
    total = float(ids["total"])

    saldo = await cliente.get(
        f"/api/v1/cxc/clientes/{ids['cliente_id']}/saldo",
        headers=auth_headers,
    )
    assert saldo.status_code == 200, saldo.text
    # Facturar no debe duplicar la deuda ya cargada por el remito.
    assert saldo.json()["saldo"] == total

    estado = await cliente.get(
        f"/api/v1/cxc/clientes/{ids['cliente_id']}/estado-cuenta",
        headers=auth_headers,
    )
    assert estado.status_code == 200
    deudas = [m for m in estado.json()["movimientos"] if m["tipo"] == "debe"]
    assert len(deudas) == 1
    assert deudas[0]["referencia_tipo"] == "remito"
    assert deudas[0]["referencia_id"] == ids["remito_id"]

    recibo = await cliente.post(
        "/api/v1/cobranzas/recibos",
        headers=auth_headers,
        json={
            "cliente_id": ids["cliente_id"],
            "monto": total,
            "medio": "efectivo",
            "imputaciones": [
                {"factura_id": ids["factura_id"], "monto": total},
            ],
        },
    )
    assert recibo.status_code == 201, recibo.text
    assert recibo.json()["monto"] == total

    saldo_final = await cliente.get(
        f"/api/v1/cxc/clientes/{ids['cliente_id']}/saldo",
        headers=auth_headers,
    )
    assert saldo_final.json()["saldo"] == 0.0

    estado_final = await cliente.get(
        f"/api/v1/cxc/clientes/{ids['cliente_id']}/estado-cuenta",
        headers=auth_headers,
    )
    assert estado_final.status_code == 200
    tipos = {m["tipo"] for m in estado_final.json()["movimientos"]}
    assert "debe" in tipos
    assert "haber" in tipos
