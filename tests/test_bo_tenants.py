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


def test_admin_siempre_tiene_todos_los_modulos(bo: TenantsBO) -> None:
    mods = bo.resolver_modulos("administrador", {"inicio": False, "mostrador": False})
    assert "configuracion" in mods
    assert set(mods) >= {
        "inicio",
        "mostrador",
        "cta_cte",
        "articulos",
        "stock",
        "clientes",
        "ventas",
        "compras",
        "configuracion",
    }


def test_vendedor_default_inicio_mostrador_cta_cte(bo: TenantsBO) -> None:
    assert bo.resolver_modulos("vendedor", None) == ["inicio", "mostrador", "cta_cte"]


def test_encargado_default_incluye_articulos_y_stock(bo: TenantsBO) -> None:
    mods = bo.resolver_modulos("encargado", None)
    assert mods == ["inicio", "mostrador", "cta_cte", "articulos", "stock"]
    assert "clientes" not in mods
    assert "configuracion" not in mods


def test_superadmin_sin_modulos_de_comercio(bo: TenantsBO) -> None:
    assert bo.resolver_modulos("superadmin", None) == []


def test_no_se_edita_rol_administrador(bo: TenantsBO) -> None:
    with pytest.raises(ReglaDeNegocioViolada, match="Vendedor y Encargado"):
        bo.validar_actualizacion_permisos("administrador", {"inicio": True})


def test_modulo_desconocido_en_matriz(bo: TenantsBO) -> None:
    with pytest.raises(ReglaDeNegocioViolada, match="no configurable"):
        bo.validar_actualizacion_permisos("vendedor", {"inicio": True, "secreto": True})
