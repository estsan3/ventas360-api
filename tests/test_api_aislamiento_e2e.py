"""Aislamiento de punta a punta: plataforma crea comercio B; A no ve a B."""

import uuid

import pytest

from app.modulos.tenants.ids import SLUG_TENANT_DEMO
from tests.conftest import ORIGIN_DEMO, PASSWORD_TEST


def _alta_comercio() -> dict:
    sufijo = uuid.uuid4().hex[:8]
    return {
        "nombre": "Kiosco E2E",
        "slug": f"e2e-{sufijo}",
        "administrador": {
            "nombre": "Ana E2E",
            "dni": "30888777",
            "email": f"ana-e2e-{sufijo}@kiosco.demo",
            "password": PASSWORD_TEST,
        },
    }


@pytest.mark.asyncio
async def test_plataforma_alta_y_comercios_no_se_ven(
    cliente, plataforma_headers, auth_headers
) -> None:
    payload = _alta_comercio()
    alta = await cliente.post(
        "/api/v1/tenants", headers=plataforma_headers, json=payload
    )
    assert alta.status_code == 201, alta.text
    slug_b = alta.json()["slug"]
    email_b = alta.json()["administrador"]["email"]
    origin_b = f"http://{slug_b}.localhost:4201"

    lista = await cliente.get("/api/v1/tenants", headers=plataforma_headers)
    slugs = {t["slug"] for t in lista.json()}
    assert SLUG_TENANT_DEMO in slugs
    assert slug_b in slugs

    login_b = await cliente.post(
        "/api/v1/auth/login",
        headers={"Origin": origin_b},
        json={"email": email_b, "password": PASSWORD_TEST},
    )
    assert login_b.status_code == 200, login_b.text
    headers_b = {
        "Authorization": f"Bearer {login_b.json()['access_token']}",
        "Origin": origin_b,
    }

    login_cruzado = await cliente.post(
        "/api/v1/auth/login",
        headers={"Origin": ORIGIN_DEMO},
        json={"email": email_b, "password": PASSWORD_TEST},
    )
    assert login_cruzado.status_code == 401

    secreto_b = f"secreto-b-{uuid.uuid4().hex[:8]}@e2e.demo"
    crear_b = await cliente.post(
        "/api/v1/clientes",
        headers=headers_b,
        json={"nombre": "Cliente secreto B", "email": secreto_b, "telefono": "1"},
    )
    assert crear_b.status_code == 201, crear_b.text
    id_b = crear_b.json()["id"]

    visto_en_a = await cliente.get(
        "/api/v1/clientes",
        headers=auth_headers,
        params={"q": secreto_b},
    )
    assert visto_en_a.status_code == 200
    assert visto_en_a.json()["total"] == 0

    get_en_a = await cliente.get(f"/api/v1/clientes/{id_b}", headers=auth_headers)
    assert get_en_a.status_code == 404

    get_en_b = await cliente.get(f"/api/v1/clientes/{id_b}", headers=headers_b)
    assert get_en_b.status_code == 200
    assert get_en_b.json()["email"] == secreto_b

    secreto_a = f"secreto-a-{uuid.uuid4().hex[:8]}@e2e.demo"
    crear_a = await cliente.post(
        "/api/v1/clientes",
        headers=auth_headers,
        json={"nombre": "Cliente secreto A", "email": secreto_a, "telefono": "1"},
    )
    assert crear_a.status_code == 201, crear_a.text
    id_a = crear_a.json()["id"]

    visto_en_b = await cliente.get(
        "/api/v1/clientes",
        headers=headers_b,
        params={"q": secreto_a},
    )
    assert visto_en_b.json()["total"] == 0

    get_a_en_b = await cliente.get(f"/api/v1/clientes/{id_a}", headers=headers_b)
    assert get_a_en_b.status_code == 404

    token_a_en_b = await cliente.get(
        "/api/v1/clientes",
        headers={**auth_headers, "Origin": origin_b},
    )
    assert token_a_en_b.status_code == 403
