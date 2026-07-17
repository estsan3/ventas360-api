"""Fixtures compartidas de los tests.

Los tests de API usan una base SQLite en memoria y el ciclo de vida real
de la aplicación (tablas), pero sin seed automático de demo.
"""

import os

os.environ["VENTAS360_DATABASE_URL"] = "sqlite+aiosqlite://"
os.environ["VENTAS360_SEED_AL_INICIAR"] = "false"
os.environ["VENTAS360_ENTORNO"] = "test"

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import fabrica_sesiones
from app.core.seguridad import hashear_password
from app.main import app
from app.modulos.auth.models import Usuario

EMAIL_TEST = "admin@ventas360.com"
PASSWORD_TEST = "demo12345"


@pytest.fixture
async def cliente():
    """Cliente HTTP contra la app, con el lifespan ejecutado (crea tablas)."""
    from asgi_lifespan import LifespanManager

    async with LifespanManager(app):
        transporte = ASGITransport(app=app)
        async with AsyncClient(transport=transporte, base_url="http://test") as http:
            yield http


@pytest.fixture
async def token_admin(cliente) -> str:
    """Crea un administrador de prueba y devuelve su token JWT."""
    async with fabrica_sesiones() as sesion:
        from app.modulos.auth.dao import UsuarioDAO

        if await UsuarioDAO(sesion).buscar_por_email(EMAIL_TEST) is None:
            sesion.add(
                Usuario(
                    nombre="Admin Test",
                    dni="11111111",
                    email=EMAIL_TEST,
                    password_hash=hashear_password(PASSWORD_TEST),
                    rol="administrador",
                )
            )
            await sesion.commit()

    respuesta = await cliente.post(
        "/api/v1/auth/login",
        json={"email": EMAIL_TEST, "password": PASSWORD_TEST},
    )
    return respuesta.json()["access_token"]


@pytest.fixture
def auth_headers(token_admin: str) -> dict[str, str]:
    """Headers con el Bearer token del admin de prueba."""
    return {"Authorization": f"Bearer {token_admin}"}
