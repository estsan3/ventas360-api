"""Cartera de cheques: cobro, entrega y arqueo por medio."""

from datetime import date, timedelta
from uuid import uuid4

import pytest

from tests.test_api_caja_sesion import _abrir


def _fecha() -> str:
    n = int(uuid4().hex[:5], 16) % (365 * 3)
    return (date(2020, 1, 1) + timedelta(days=n)).isoformat()


def _tag() -> str:
    return uuid4().hex[:8]


async def _setup_deuda(cliente, auth_headers) -> dict[str, str]:
    tag = _tag()
    cli = await cliente.post(
        "/api/v1/clientes",
        headers=auth_headers,
        json={
            "nombre": f"Cheque Demo {tag}",
            "email": f"chq-{tag}@demo.com",
            "telefono": "1",
        },
    )
    assert cli.status_code == 201, cli.text
    cliente_id = cli.json()["id"]

    prod = await cliente.post(
        "/api/v1/productos",
        headers=auth_headers,
        json={
            "sku": f"CHQ-{tag}",
            "nombre": "Art Cheque",
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
        json={"codigo": f"CHQ-{tag}"[:12], "nombre": "Dep Cheque"},
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
    conf = await cliente.post(
        f"/api/v1/ventas/pedidos/{remito_id}/confirmar-remito",
        headers=auth_headers,
    )
    assert conf.status_code == 200, conf.text
    factura = await cliente.post(
        f"/api/v1/ventas/pedidos/{remito_id}/facturar",
        headers=auth_headers,
    )
    assert factura.status_code == 200, factura.text
    return {
        "cliente_id": cliente_id,
        "factura_id": factura.json()["id"],
        "total": str(factura.json()["total"]),
        "nombre": f"Cheque Demo {tag}",
    }


@pytest.mark.asyncio
async def test_cobro_cheque_entra_a_cartera_y_no_a_efectivo(
    cliente, auth_headers
) -> None:
    ids = await _setup_deuda(cliente, auth_headers)
    total = float(ids["total"])
    fecha = _fecha()
    await _abrir(cliente, auth_headers, fecha, 500)

    recibo = await cliente.post(
        "/api/v1/cobranzas/recibos",
        headers=auth_headers,
        json={
            "cliente_id": ids["cliente_id"],
            "monto": total,
            "medio": "cheque",
            "fecha": fecha,
            "imputaciones": [{"factura_id": ids["factura_id"], "monto": total}],
            "cheque": {
                "numero": "884421",
                "banco_emisor": "Galicia",
                "librador": ids["nombre"],
                "recibido_de": ids["nombre"],
            },
        },
    )
    assert recibo.status_code == 201, recibo.text
    assert recibo.json()["medio"] == "cheque"

    valores = await cliente.get("/api/v1/bancos/valores", headers=auth_headers)
    assert valores.status_code == 200
    cartera = [v for v in valores.json() if v["numero"] == "884421"]
    assert len(cartera) == 1
    assert cartera[0]["estado"] == "en_cartera"
    assert cartera[0]["monto"] == total
    assert cartera[0]["banco_emisor"] == "Galicia"

    saldo = await cliente.get(
        "/api/v1/caja/saldo",
        headers=auth_headers,
        params={"fecha": fecha},
    )
    assert saldo.status_code == 200
    body = saldo.json()
    assert body["efectivo_esperado"] == 500
    assert body["cheques_esperado"] == total
    assert body["tarjetas_esperado"] == 0

    cierre = await cliente.post(
        "/api/v1/caja/cerrar",
        headers=auth_headers,
        json={
            "efectivo_contado": 500,
            "cheques_contado": total,
            "tarjetas_contado": 0,
            "fecha": fecha,
        },
    )
    assert cierre.status_code == 200, cierre.text
    cerrado = cierre.json()
    assert cerrado["estado"] == "cerrada"
    assert cerrado["diferencia"] == 0
    assert cerrado["cheques_contado"] == total
    assert cerrado["cheques_diferencia"] == 0


@pytest.mark.asyncio
async def test_egreso_con_cheque_de_cartera(cliente, auth_headers) -> None:
    fecha = _fecha()
    await _abrir(cliente, auth_headers, fecha, 100)

    valor = await cliente.post(
        "/api/v1/bancos/valores",
        headers=auth_headers,
        json={
            "tipo": "cheque_tercero",
            "monto": 250,
            "numero": "11002",
            "banco_emisor": "Nación",
            "librador": "Proveedor SA",
            "recibido_de": "Cliente X",
        },
    )
    assert valor.status_code == 201, valor.text
    valor_id = valor.json()["id"]

    egreso = await cliente.post(
        "/api/v1/caja/movimientos",
        headers=auth_headers,
        json={
            "tipo": "egreso",
            "medio": "cheque",
            "monto": 250,
            "concepto": "Pago proveedor",
            "fecha": fecha,
            "cheque_id": valor_id,
            "entregado_a": "Proveedor SA",
        },
    )
    assert egreso.status_code == 201, egreso.text
    assert egreso.json()["medio"] == "cheque"

    detalle = await cliente.get("/api/v1/bancos/valores", headers=auth_headers)
    item = next(v for v in detalle.json() if v["id"] == valor_id)
    assert item["estado"] == "entregado"
    assert item["entregado_a"] == "Proveedor SA"

    saldo = await cliente.get(
        "/api/v1/caja/saldo",
        headers=auth_headers,
        params={"fecha": fecha},
    )
    assert saldo.json()["cheques_esperado"] == -250


@pytest.mark.asyncio
async def test_entregar_y_emitir_cheque_propio(cliente, auth_headers) -> None:
    fecha = _fecha()
    await _abrir(cliente, auth_headers, fecha, 0)

    propio = await cliente.post(
        "/api/v1/caja/movimientos",
        headers=auth_headers,
        json={
            "tipo": "egreso",
            "medio": "cheque",
            "monto": 80,
            "concepto": "Alquiler",
            "fecha": fecha,
            "cheque": {
                "numero": "9001",
                "banco_emisor": "Santander",
                "destinatario": "Inmobiliaria Sur",
            },
            "entregado_a": "Inmobiliaria Sur",
        },
    )
    assert propio.status_code == 201, propio.text

    valores = await cliente.get("/api/v1/bancos/valores", headers=auth_headers)
    emitido = next(v for v in valores.json() if v["numero"] == "9001")
    assert emitido["tipo"] == "cheque_propio"
    assert emitido["estado"] == "entregado"
    assert emitido["entregado_a"] == "Inmobiliaria Sur"

    tercero = await cliente.post(
        "/api/v1/bancos/valores",
        headers=auth_headers,
        json={
            "tipo": "cheque_tercero",
            "monto": 40,
            "numero": "3301",
            "banco_emisor": "Macro",
            "librador": "Juan",
        },
    )
    assert tercero.status_code == 201, tercero.text
    entrega = await cliente.post(
        f"/api/v1/bancos/valores/{tercero.json()['id']}/entregar",
        headers=auth_headers,
        json={"destinatario": "Flete Norte"},
    )
    assert entrega.status_code == 200, entrega.text
    assert entrega.json()["estado"] == "entregado"
    assert entrega.json()["entregado_a"] == "Flete Norte"


@pytest.mark.asyncio
async def test_cobro_mixto_efectivo_y_cheque(cliente, auth_headers) -> None:
    ids = await _setup_deuda(cliente, auth_headers)
    total = float(ids["total"])
    fecha = _fecha()
    await _abrir(cliente, auth_headers, fecha, 500)
    efectivo = 100.0
    cheque = round(total - efectivo, 2)

    recibo = await cliente.post(
        "/api/v1/cobranzas/recibos",
        headers=auth_headers,
        json={
            "cliente_id": ids["cliente_id"],
            "monto": total,
            "fecha": fecha,
            "imputaciones": [{"factura_id": ids["factura_id"], "monto": total}],
            "medios": [
                {"medio": "efectivo", "monto": efectivo},
                {
                    "medio": "cheque",
                    "monto": cheque,
                    "cheque": {
                        "numero": "MIX-77",
                        "banco_emisor": "Nación",
                        "librador": ids["nombre"],
                        "recibido_de": ids["nombre"],
                    },
                },
            ],
        },
    )
    assert recibo.status_code == 201, recibo.text
    assert recibo.json()["medio"] == "mixto"
    assert recibo.json()["monto"] == total

    valores = await cliente.get("/api/v1/bancos/valores", headers=auth_headers)
    cartera = [v for v in valores.json() if v["numero"] == "MIX-77"]
    assert len(cartera) == 1
    assert cartera[0]["monto"] == cheque

    saldo = await cliente.get(
        "/api/v1/caja/saldo",
        headers=auth_headers,
        params={"fecha": fecha},
    )
    assert saldo.status_code == 200
    body = saldo.json()
    assert body["efectivo_esperado"] == 600
    assert body["cheques_esperado"] == cheque

    cxc = await cliente.get(
        f"/api/v1/cxc/clientes/{ids['cliente_id']}/saldo",
        headers=auth_headers,
    )
    assert cxc.json()["saldo"] == 0.0
