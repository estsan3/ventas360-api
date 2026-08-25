"""Tests unitarios del BO de tenants (slug y host)."""

import pytest

from app.core.excepciones import ReglaDeNegocioViolada
from app.modulos.tenants.bo import TIPO_COMERCIO, TIPO_PLATAFORMA, TIPO_SIN_SLUG, TenantsBO


@pytest.fixture
def bo() -> TenantsBO:
    return TenantsBO()


def test_slug_valido(bo: TenantsBO) -> None:
    assert bo.validar_slug("AgroNorte") == "agronorte"
    assert bo.validar_slug("kiosco-milka") == "kiosco-milka"


def test_slug_reservado_admin(bo: TenantsBO) -> None:
    with pytest.raises(ReglaDeNegocioViolada, match="reservado"):
        bo.validar_slug("admin")


def test_slug_invalido(bo: TenantsBO) -> None:
    with pytest.raises(ReglaDeNegocioViolada, match="minúsculas"):
        bo.validar_slug("Ferretería AgroNorte")
    with pytest.raises(ReglaDeNegocioViolada, match="minúsculas"):
        bo.validar_slug("-milka")


def test_nombre_vacio(bo: TenantsBO) -> None:
    with pytest.raises(ReglaDeNegocioViolada, match="obligatorio"):
        bo.validar_nombre("   ")


def test_clasificar_plataforma(bo: TenantsBO) -> None:
    tipo, slug = bo.clasificar_host("admin.localhost:4201")
    assert tipo == TIPO_PLATAFORMA
    assert slug is None


def test_clasificar_comercio(bo: TenantsBO) -> None:
    tipo, slug = bo.clasificar_host("agronorte.localhost:4201")
    assert tipo == TIPO_COMERCIO
    assert slug == "agronorte"


def test_clasificar_sin_subdominio(bo: TenantsBO) -> None:
    tipo, slug = bo.clasificar_host("localhost:4201")
    assert tipo == TIPO_SIN_SLUG
    assert slug is None
    tipo_ip, _ = bo.clasificar_host("127.0.0.1:8001")
    assert tipo_ip == TIPO_SIN_SLUG


def test_extraer_de_origin_con_esquema(bo: TenantsBO) -> None:
    assert bo.extraer_etiqueta("http://milka.localhost:4201/") == "milka"
