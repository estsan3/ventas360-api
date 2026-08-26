"""Contexto de tenant según Origin / Host."""

import pytest

from app.core.database import fabrica_sesiones
from app.modulos.tenants.models import Tenant


@pytest.mark.asyncio
async def test_contexto_plataforma_por_origin(cliente) -> None:
    respuesta = await cliente.get(
        "/api/v1/tenants/contexto",
        headers={"Origin": "http://admin.localhost:4201"},
    )
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["tipo"] == "plataforma"
    assert cuerpo["tenant"] is None


@pytest.mark.asyncio
async def test_contexto_comercio_existente(cliente) -> None:
    async with fabrica_sesiones() as sesion:
        sesion.add(
            Tenant(
                id="tnt-agronorte",
                slug="agronorte",
                nombre="Ferretería AgroNorte",
            )
        )
        await sesion.commit()

    respuesta = await cliente.get(
        "/api/v1/tenants/contexto",
        headers={"Origin": "http://agronorte.localhost:4201"},
    )
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["tipo"] == "comercio"
    assert cuerpo["slug"] == "agronorte"
    assert cuerpo["tenant"]["nombre"] == "Ferretería AgroNorte"


@pytest.mark.asyncio
async def test_contexto_comercio_desconocido(cliente) -> None:
    respuesta = await cliente.get(
        "/api/v1/tenants/contexto",
        headers={"X-Forwarded-Host": "milka.localhost:4201"},
    )
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["tipo"] == "comercio"
    assert cuerpo["slug"] == "milka"
    assert cuerpo["tenant"] is None


@pytest.mark.asyncio
async def test_contexto_comercio_por_referer(cliente) -> None:
    async with fabrica_sesiones() as sesion:
        sesion.add(
            Tenant(
                id="tnt-referer",
                slug="referer-demo",
                nombre="Kiosco Referer",
            )
        )
        await sesion.commit()

    respuesta = await cliente.get(
        "/api/v1/tenants/contexto",
        headers={
            "Origin": "",
            "Referer": "http://referer-demo.localhost:4201/login",
        },
    )
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["tipo"] == "comercio"
    assert cuerpo["slug"] == "referer-demo"
    assert cuerpo["tenant"]["nombre"] == "Kiosco Referer"


@pytest.mark.asyncio
async def test_contexto_localhost_sin_slug(cliente) -> None:
    respuesta = await cliente.get(
        "/api/v1/tenants/contexto",
        headers={"Origin": "http://localhost:4201"},
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["tipo"] == "sin_slug"
