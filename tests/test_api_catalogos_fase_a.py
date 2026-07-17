"""Integración: listados paginados Fase A (clientes / productos)."""

import pytest


@pytest.mark.asyncio
async def test_listar_productos_paginado(cliente, auth_headers) -> None:
    crear = await cliente.post(
        "/api/v1/productos",
        headers=auth_headers,
        json={
            "sku": "FASE-A-001",
            "nombre": "Producto paginación",
            "marca": "Demo",
            "rubro": "Test",
            "codigo_barras": "1234567890123",
            "costo": 10,
            "precio": 20,
            "stock": 5,
        },
    )
    assert crear.status_code == 201, crear.text

    lista = await cliente.get(
        "/api/v1/productos",
        headers=auth_headers,
        params={"q": "paginación", "page": 1, "page_size": 10},
    )
    assert lista.status_code == 200
    body = lista.json()
    assert body["total"] >= 1
    assert any(p["sku"] == "FASE-A-001" for p in body["items"])


@pytest.mark.asyncio
async def test_crear_cliente_con_datos_fiscales(cliente, auth_headers) -> None:
    respuesta = await cliente.post(
        "/api/v1/clientes",
        headers=auth_headers,
        json={
            "nombre": "Cliente Fiscal",
            "email": "fiscal@demo.com",
            "telefono": "111",
            "cuit": "20123456789",
            "condicion_iva": "responsable_inscripto",
            "limite_credito": 10000,
        },
    )
    assert respuesta.status_code == 201, respuesta.text
    data = respuesta.json()
    assert data["cuit"] == "20123456789"
    assert data["condicion_iva"] == "responsable_inscripto"

    pagina = await cliente.get(
        "/api/v1/clientes",
        headers=auth_headers,
        params={"q": "Fiscal", "activo": True},
    )
    assert pagina.status_code == 200
    assert pagina.json()["total"] >= 1
