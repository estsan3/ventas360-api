"""Apertura, egreso y cierre de caja con arqueo."""

from datetime import date, timedelta
from uuid import uuid4

import pytest


def _fecha() -> str:
    n = int(uuid4().hex[:5], 16) % (365 * 3)
    return (date(2020, 1, 1) + timedelta(days=n)).isoformat()


async def _abrir(cliente, auth_headers, fecha: str, fondo: float = 1000) -> None:
    resp = await cliente.post(
        "/api/v1/caja/abrir",
        headers=auth_headers,
        json={"fondo_inicial": fondo, "fecha": fecha},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["estado"] == "abierta"
    assert body["fondo_inicial"] == fondo


@pytest.mark.asyncio
async def test_egreso_sin_abrir_falla(cliente, auth_headers) -> None:
    fecha = _fecha()
    resp = await cliente.post(
        "/api/v1/caja/movimientos",
        headers=auth_headers,
        json={
            "tipo": "egreso",
            "medio": "efectivo",
            "monto": 50,
            "concepto": "Flete",
            "fecha": fecha,
        },
    )
    assert resp.status_code == 422
    assert "abierta" in resp.json()["error"]["mensaje"].lower()


@pytest.mark.asyncio
async def test_abrir_egreso_y_cerrar_con_arqueo(cliente, auth_headers) -> None:
    fecha = _fecha()
    await _abrir(cliente, auth_headers, fecha, 1000)

    movs = await cliente.get(
        "/api/v1/caja/movimientos",
        headers=auth_headers,
        params={"fecha": fecha},
    )
    assert movs.status_code == 200
    fondo = next(m for m in movs.json() if m["referencia_tipo"] == "apertura")
    assert fondo["monto"] == 1000
    assert fondo["tipo"] == "ingreso"

    egreso = await cliente.post(
        "/api/v1/caja/movimientos",
        headers=auth_headers,
        json={
            "tipo": "egreso",
            "medio": "efectivo",
            "monto": 200,
            "concepto": "Pago flete",
            "fecha": fecha,
        },
    )
    assert egreso.status_code == 201, egreso.text

    saldo = await cliente.get(
        "/api/v1/caja/saldo",
        headers=auth_headers,
        params={"fecha": fecha},
    )
    assert saldo.status_code == 200
    assert saldo.json()["efectivo_esperado"] == 800

    cierre = await cliente.post(
        "/api/v1/caja/cerrar",
        headers=auth_headers,
        json={"efectivo_contado": 790, "fecha": fecha},
    )
    assert cierre.status_code == 200, cierre.text
    body = cierre.json()
    assert body["estado"] == "cerrada"
    assert body["efectivo_contado"] == 790
    assert body["diferencia"] == -10

    otra = await cliente.post(
        "/api/v1/caja/movimientos",
        headers=auth_headers,
        json={
            "tipo": "egreso",
            "medio": "efectivo",
            "monto": 10,
            "concepto": "Extra",
            "fecha": fecha,
        },
    )
    assert otra.status_code == 422


@pytest.mark.asyncio
async def test_no_abre_dos_veces_ni_egreso_sin_fondo(cliente, auth_headers) -> None:
    fecha = _fecha()
    await _abrir(cliente, auth_headers, fecha, 100)
    dup = await cliente.post(
        "/api/v1/caja/abrir",
        headers=auth_headers,
        json={"fondo_inicial": 50, "fecha": fecha},
    )
    assert dup.status_code == 422

    corto = await cliente.post(
        "/api/v1/caja/movimientos",
        headers=auth_headers,
        json={
            "tipo": "egreso",
            "medio": "efectivo",
            "monto": 150,
            "concepto": "Retiro",
            "fecha": fecha,
        },
    )
    assert corto.status_code == 422
    assert "suficiente" in corto.json()["error"]["mensaje"].lower()


@pytest.mark.asyncio
async def test_cerrar_permite_abrir_otro_turno(cliente, auth_headers) -> None:
    fecha = _fecha()
    await _abrir(cliente, auth_headers, fecha, 1000)
    cierre = await cliente.post(
        "/api/v1/caja/cerrar",
        headers=auth_headers,
        json={"efectivo_contado": 1000, "fecha": fecha},
    )
    assert cierre.status_code == 200, cierre.text
    assert cierre.json()["estado"] == "cerrada"

    segunda = await cliente.post(
        "/api/v1/caja/abrir",
        headers=auth_headers,
        json={"fondo_inicial": 400, "fecha": fecha},
    )
    assert segunda.status_code == 200, segunda.text
    body = segunda.json()
    assert body["estado"] == "abierta"
    assert body["fondo_inicial"] == 400
    assert body["efectivo_esperado"] == 400

    movs = await cliente.get(
        "/api/v1/caja/movimientos",
        headers=auth_headers,
        params={"fecha": fecha},
    )
    assert movs.status_code == 200
    fondos = [m for m in movs.json() if m["referencia_tipo"] == "apertura"]
    assert len(fondos) == 1
    assert fondos[0]["monto"] == 400
