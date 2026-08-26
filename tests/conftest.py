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
from app.modulos.tenants.ids import (
    EMAIL_SUPERADMIN,
    ID_TENANT_DEMO,
    ID_USUARIO_SUPERADMIN,
    NOMBRE_TENANT_DEMO,
    SLUG_TENANT_DEMO,
)
from app.modulos.tenants.models import Tenant

EMAIL_TEST = "admin@ventas360.com"
PASSWORD_TEST = "demo12345"
ORIGIN_DEMO = "http://demo.localhost:4201"
ORIGIN_PLATAFORMA = "http://admin.localhost:4201"


@pytest.fixture
async def cliente():
    """Cliente HTTP contra la app, con el lifespan ejecutado (crea tablas)."""
    from asgi_lifespan import LifespanManager

    async with LifespanManager(app):
        async with fabrica_sesiones() as sesion:
            if await sesion.get(Tenant, ID_TENANT_DEMO) is None:
                sesion.add(
                    Tenant(
                        id=ID_TENANT_DEMO,
                        slug=SLUG_TENANT_DEMO,
                        nombre=NOMBRE_TENANT_DEMO,
                    )
                )
                await sesion.commit()
        transporte = ASGITransport(app=app)
        async with AsyncClient(
            transport=transporte,
            base_url="http://test",
            headers={"Origin": ORIGIN_DEMO},
        ) as http:
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
                    tenant_id=ID_TENANT_DEMO,
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


@pytest.fixture
async def token_superadmin(cliente) -> str:
    """Crea un superadmin de plataforma y devuelve su token JWT."""
    async with fabrica_sesiones() as sesion:
        from app.modulos.auth.dao import UsuarioDAO

        if await UsuarioDAO(sesion).buscar_por_email(EMAIL_SUPERADMIN) is None:
            sesion.add(
                Usuario(
                    id=ID_USUARIO_SUPERADMIN,
                    nombre="Superadmin Plataforma",
                    dni="00000000",
                    email=EMAIL_SUPERADMIN,
                    password_hash=hashear_password(PASSWORD_TEST),
                    rol="superadmin",
                    tenant_id=None,
                )
            )
            await sesion.commit()

    respuesta = await cliente.post(
        "/api/v1/auth/login",
        json={"email": EMAIL_SUPERADMIN, "password": PASSWORD_TEST},
        headers={"Origin": ORIGIN_PLATAFORMA},
    )
    return respuesta.json()["access_token"]


@pytest.fixture
def plataforma_headers(token_superadmin: str) -> dict[str, str]:
    """Bearer de superadmin + Origin de plataforma."""
    return {
        "Authorization": f"Bearer {token_superadmin}",
        "Origin": ORIGIN_PLATAFORMA,
    }
