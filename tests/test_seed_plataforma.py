"""Seed de plataforma: superadmin entra en admin.*."""

import pytest

from app.core.database import fabrica_sesiones
from app.modulos.auth.dao import UsuarioDAO
from app.modulos.tenants.ids import EMAIL_SUPERADMIN, ID_USUARIO_SUPERADMIN
from scripts.seed import PASSWORD_DEMO, _asegurar_superadmin_plataforma
from tests.conftest import ORIGIN_PLATAFORMA


@pytest.mark.asyncio
async def test_seed_superadmin_loguea_en_plataforma(cliente) -> None:
    async with fabrica_sesiones() as sesion:
        await _asegurar_superadmin_plataforma(sesion)
        await _asegurar_superadmin_plataforma(sesion)
        usuario = await UsuarioDAO(sesion).buscar_por_email(EMAIL_SUPERADMIN)
        assert usuario is not None
        assert usuario.id == ID_USUARIO_SUPERADMIN
        assert usuario.rol == "superadmin"
        assert usuario.tenant_id is None

    login = await cliente.post(
        "/api/v1/auth/login",
        headers={"Origin": ORIGIN_PLATAFORMA},
        json={"email": EMAIL_SUPERADMIN, "password": PASSWORD_DEMO},
    )
    assert login.status_code == 200, login.text
    cuerpo = login.json()["usuario"]
    assert cuerpo["rol"] == "superadmin"
    assert cuerpo["tenant_id"] is None

    tenants = await cliente.get(
        "/api/v1/tenants",
        headers={
            "Authorization": f"Bearer {login.json()['access_token']}",
            "Origin": ORIGIN_PLATAFORMA,
        },
    )
    assert tenants.status_code == 200
    assert any(t["slug"] == "demo" for t in tenants.json())
