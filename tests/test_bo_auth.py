"""Tests unitarios del BO de auth (sin DB)."""

import pytest

from app.core.excepciones import NoAutenticado, ReglaDeNegocioViolada
from app.core.seguridad import hashear_password
from app.modulos.auth.bo import UsuarioBO


@pytest.fixture
def bo() -> UsuarioBO:
    return UsuarioBO()


def test_credenciales_usuario_inexistente(bo: UsuarioBO) -> None:
    with pytest.raises(NoAutenticado):
        bo.validar_credenciales(None, "cualquier")


def test_credenciales_password_incorrecta(bo: UsuarioBO) -> None:
    hash_ok = hashear_password("secreta")
    with pytest.raises(NoAutenticado):
        bo.validar_credenciales(hash_ok, "otra")


def test_credenciales_ok(bo: UsuarioBO) -> None:
    hash_ok = hashear_password("secreta")
    bo.validar_credenciales(hash_ok, "secreta")


def test_alta_rol_invalido(bo: UsuarioBO) -> None:
    with pytest.raises(ReglaDeNegocioViolada, match="Rol inválido"):
        bo.validar_alta(email_ya_registrado=False, rol="superuser")


def test_alta_encargado_ok(bo: UsuarioBO) -> None:
    bo.validar_alta(email_ya_registrado=False, rol="encargado")


def test_baja_ultimo_admin(bo: UsuarioBO) -> None:
    with pytest.raises(ReglaDeNegocioViolada, match="último administrador"):
        bo.validar_baja(es_el_mismo_usuario=False, es_ultimo_administrador=True)


def test_login_host_plataforma_superadmin(bo: UsuarioBO) -> None:
    bo.validar_login_host(
        tenant_id_usuario=None,
        rol="superadmin",
        tipo_host="plataforma",
        tenant_id_host=None,
    )


def test_login_host_plataforma_rechaza_comercio(bo: UsuarioBO) -> None:
    with pytest.raises(NoAutenticado, match="plataforma"):
        bo.validar_login_host(
            tenant_id_usuario="tnt-demo",
            rol="administrador",
            tipo_host="plataforma",
            tenant_id_host=None,
        )


def test_login_host_comercio_ok(bo: UsuarioBO) -> None:
    bo.validar_login_host(
        tenant_id_usuario="tnt-demo",
        rol="administrador",
        tipo_host="comercio",
        tenant_id_host="tnt-demo",
    )


def test_login_host_comercio_ajeno(bo: UsuarioBO) -> None:
    with pytest.raises(NoAutenticado, match="no pertenece"):
        bo.validar_login_host(
            tenant_id_usuario="tnt-demo",
            rol="administrador",
            tipo_host="comercio",
            tenant_id_host="tnt-milka",
        )


def test_login_host_sin_slug(bo: UsuarioBO) -> None:
    with pytest.raises(NoAutenticado, match="subdominio"):
        bo.validar_login_host(
            tenant_id_usuario="tnt-demo",
            rol="administrador",
            tipo_host="sin_slug",
            tenant_id_host=None,
        )
