"""Integración endpoints IA."""

import pytest


@pytest.mark.asyncio
async def test_interpretar_mostrador_mock(cliente, auth_headers) -> None:
    resp = await cliente.post(
        "/api/v1/ai/mostrador/interpretar",
        headers=auth_headers,
        json={"texto": "2 mouse para Distribuidora Norte"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["modo_parser"] == "mock"
    assert len(body["lineas"]) >= 1


@pytest.mark.asyncio
async def test_acciones_del_dia(cliente, auth_headers) -> None:
    resp = await cliente.get("/api/v1/ai/acciones", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "acciones" in body
    assert isinstance(body["acciones"], list)


@pytest.mark.asyncio
async def test_resumen_dia(cliente, auth_headers) -> None:
    resp = await cliente.get(
        "/api/v1/ai/resumen-dia",
        headers=auth_headers,
        params={"narrativa": "true"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["metricas"]["moneda"]
    assert body["narrativa"]


@pytest.mark.asyncio
async def test_webhook_requiere_secreto(cliente) -> None:
    resp = await cliente.get(
        "/api/v1/ai/webhook/resumen-dia",
        headers={"X-Tenant-Slug": "demo"},
    )
    assert resp.status_code == 401
