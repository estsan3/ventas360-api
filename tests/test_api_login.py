"""Test de login contra la API."""

import pytest

from tests.conftest import EMAIL_TEST, PASSWORD_TEST


@pytest.mark.asyncio
async def test_login_con_usuario_seeded(cliente, token_admin):
    """Login exitoso con el usuario creado en el fixture."""
    assert token_admin

    respuesta = await cliente.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token_admin}"},
    )
    assert respuesta.status_code == 200
    perfil = respuesta.json()
    assert perfil["email"] == EMAIL_TEST
    assert perfil["rol"] == "administrador"


@pytest.mark.asyncio
async def test_login_credenciales_invalidas(cliente):
    """Credenciales incorrectas devuelven 401."""
    respuesta = await cliente.post(
        "/api/v1/auth/login",
        json={"email": EMAIL_TEST, "password": "incorrecta"},
    )
    assert respuesta.status_code == 401


@pytest.mark.asyncio
async def test_login_setea_cookie_y_me_con_cookie(cliente, token_admin):
    """Login deja cookie httpOnly; /me acepta la cookie sin Bearer."""
    assert token_admin
    login = await cliente.post(
        "/api/v1/auth/login",
        json={"email": EMAIL_TEST, "password": PASSWORD_TEST},
    )
    assert login.status_code == 200
    assert "ventas360_access_token" in login.cookies

    me = await cliente.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == EMAIL_TEST
