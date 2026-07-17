"""Integración A8–A9: parámetros operativos y KPIs reales."""

import pytest


@pytest.mark.asyncio
async def test_operativos_y_talonarios(cliente, auth_headers) -> None:
    ops = await cliente.put(
        "/api/v1/parametros/operativos",
        headers=auth_headers,
        json={
            "sucursal_codigo": "SUC1",
            "sucursal_nombre": "Sucursal Uno",
            "condiciones_pago": ["contado", "45_dias"],
        },
    )
    assert ops.status_code == 200, ops.text
    assert ops.json()["sucursal_codigo"] == "SUC1"

    tal = await cliente.put(
        "/api/v1/parametros/talonarios",
        headers=auth_headers,
        json={
            "tipo_comprobante": "remito",
            "prefijo": "R-",
            "proximo_numero": 10,
            "activo": True,
        },
    )
    assert tal.status_code == 200, tal.text
    assert tal.json()["proximo_numero"] == 10

    lista = await cliente.get("/api/v1/parametros/talonarios", headers=auth_headers)
    assert lista.status_code == 200
    assert any(t["tipo_comprobante"] == "remito" for t in lista.json())


@pytest.mark.asyncio
async def test_kpis_incluye_campos_fase_a(cliente, auth_headers) -> None:
    # Seed mínimo vía alta cliente/producto para tener conteos > 0
    await cliente.post(
        "/api/v1/clientes",
        headers=auth_headers,
        json={"nombre": "KPI Cli", "email": "kpi@demo.com", "telefono": "1"},
    )
    await cliente.post(
        "/api/v1/productos",
        headers=auth_headers,
        json={
            "sku": "KPI-1",
            "nombre": "Prod KPI",
            "precio": 10,
            "stock": 1,
        },
    )

    kpis = await cliente.get("/api/v1/reporteria/kpis", headers=auth_headers)
    assert kpis.status_code == 200, kpis.text
    body = kpis.json()
    assert body["clientes_activos"] >= 1
    assert body["productos_activos"] >= 1
    assert "monto_ventas_dia" in body
    assert "remitos_pendientes" in body
    assert "top_articulos" in body
    assert isinstance(body["top_articulos"], list)
