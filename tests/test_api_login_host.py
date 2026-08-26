"""Login atado al Host: comercio vs plataforma."""

import pytest

from app.core.database import fabrica_sesiones
from app.core.seguridad import hashear_password
from app.core.tenant_ctx import usando_tenant
from app.modulos.auth.models import Usuario
from app.modulos.tenants.ids import ID_TENANT_DEMO
from app.modulos.tenants.models import Tenant
from tests.conftest import (
    EMAIL_SUPERADMIN,
    EMAIL_TEST,
    ORIGIN_DEMO,
    ORIGIN_PLATAFORMA,
    PASSWORD_TEST,
)

ID_MILKA = "tnt-login-milka"
EMAIL_MILKA = "ana-login@milka.demo"
ORIGIN_MILKA = "http://login-milka.localhost:4201"


async def _sembrar_milka() -> None:
    async with fabrica_sesiones() as sesion:
        if await sesion.get(Tenant, ID_MILKA) is None:
            sesion.add(
                Tenant(id=ID_MILKA, slug="login-milka", nombre="Kiosco Login Milka")
            )
        with usando_tenant(ID_MILKA):
            if await sesion.get(Usuario, "usr-login-milka") is None:
                sesion.add(
                    Usuario(
                        id="usr-login-milka",
                        tenant_id=ID_MILKA,
                        nombre="Ana Login",
                        dni="30111000",
                        email=EMAIL_MILKA,
                        password_hash=hashear_password(PASSWORD_TEST),
                        rol="administrador",
                    )
                )
            await sesion.commit()


@pytest.mark.asyncio
async def test_admin_demo_entra_en_su_host(cliente, token_admin) -> None:
    login = await cliente.post(
        "/api/v1/auth/login",
        json={"email": EMAIL_TEST, "password": PASSWORD_TEST},
    )
    assert login.status_code == 200
    cuerpo = login.json()
    assert cuerpo["usuario"]["tenant_id"] == ID_TENANT_DEMO
    assert cuerpo["usuario"]["rol"] == "administrador"


@pytest.mark.asyncio
async def test_admin_demo_no_entra_en_plataforma(cliente, token_admin) -> None:
    login = await cliente.post(
        "/api/v1/auth/login",
        headers={"Origin": ORIGIN_PLATAFORMA},
        json={"email": EMAIL_TEST, "password": PASSWORD_TEST},
    )
    assert login.status_code == 401
    assert "plataforma" in login.json()["error"]["mensaje"].lower()


@pytest.mark.asyncio
async def test_admin_demo_no_entra_en_otro_comercio(cliente, token_admin) -> None:
    await _sembrar_milka()
    login = await cliente.post(
        "/api/v1/auth/login",
        headers={"Origin": ORIGIN_MILKA},
        json={"email": EMAIL_TEST, "password": PASSWORD_TEST},
    )
    assert login.status_code == 401
    assert "no pertenece" in login.json()["error"]["mensaje"].lower()


@pytest.mark.asyncio
async def test_superadmin_entra_en_plataforma(cliente, token_superadmin) -> None:
    login = await cliente.post(
        "/api/v1/auth/login",
        headers={"Origin": ORIGIN_PLATAFORMA},
        json={"email": EMAIL_SUPERADMIN, "password": PASSWORD_TEST},
    )
    assert login.status_code == 200
    assert login.json()["usuario"]["rol"] == "superadmin"
    assert login.json()["usuario"]["tenant_id"] is None


@pytest.mark.asyncio
async def test_superadmin_no_entra_en_comercio(cliente, token_superadmin) -> None:
    login = await cliente.post(
        "/api/v1/auth/login",
        headers={"Origin": ORIGIN_DEMO},
        json={"email": EMAIL_SUPERADMIN, "password": PASSWORD_TEST},
    )
    assert login.status_code == 401
    assert "no pertenece" in login.json()["error"]["mensaje"].lower()


@pytest.mark.asyncio
async def test_token_demo_en_otro_comercio_es_403(cliente, auth_headers) -> None:
    await _sembrar_milka()
    respuesta = await cliente.get(
        "/api/v1/clientes",
        headers={**auth_headers, "Origin": ORIGIN_MILKA},
    )
    assert respuesta.status_code == 403
    assert respuesta.json()["error"]["codigo"] == "no_autorizado"


@pytest.mark.asyncio
async def test_me_respeta_el_host(cliente, token_admin) -> None:
    ok = await cliente.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token_admin}"},
    )
    assert ok.status_code == 200
    assert ok.json()["tenant_id"] == ID_TENANT_DEMO

    ajeno = await cliente.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {token_admin}",
            "Origin": ORIGIN_PLATAFORMA,
        },
    )
    assert ajeno.status_code == 401
