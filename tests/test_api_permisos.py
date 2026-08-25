"""Matriz de módulos: vendedor/encargado 403 vs catálogo 200."""

import pytest

from app.modulos.tenants.bo import DEFAULTS_HABILITADOS, MODULOS_MATRIZ
from tests.conftest import PASSWORD_TEST


async def _alta_y_login(cliente, auth_headers, *, rol: str, email: str) -> dict[str, str]:
    alta = await cliente.post(
        "/api/v1/usuarios",
        headers=auth_headers,
        json={
            "nombre": rol.title(),
            "dni": "30111000",
            "email": email,
            "password": PASSWORD_TEST,
            "rol": rol,
        },
    )
    assert alta.status_code == 201, alta.text
    login = await cliente.post(
        "/api/v1/auth/login",
        json={"email": email, "password": PASSWORD_TEST},
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def _reset_matriz(cliente, auth_headers) -> None:
    for rol in ("vendedor", "encargado"):
        defaults = DEFAULTS_HABILITADOS[rol]
        respuesta = await cliente.put(
            "/api/v1/tenants/permisos",
            headers=auth_headers,
            json={
                "rol": rol,
                "modulos": {m: m in defaults for m in MODULOS_MATRIZ},
            },
        )
        assert respuesta.status_code == 200, respuesta.text


@pytest.mark.asyncio
async def test_me_admin_incluye_permisos_y_configuracion(cliente, token_admin) -> None:
    me = await cliente.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token_admin}"},
    )
    assert me.status_code == 200
    permisos = me.json()["permisos"]
    assert "configuracion" in permisos
    assert "articulos" in permisos
    assert "clientes" in permisos


@pytest.mark.asyncio
async def test_vendedor_catalogo_si_abm_no(cliente, auth_headers) -> None:
    await _reset_matriz(cliente, auth_headers)
    headers = await _alta_y_login(
        cliente, auth_headers, rol="vendedor", email="vend-matriz@ventas360.com"
    )
    me = await cliente.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert set(me.json()["permisos"]) == {"inicio", "mostrador", "cta_cte"}

    assert (await cliente.get("/api/v1/productos", headers=headers)).status_code == 200
    assert (await cliente.get("/api/v1/clientes", headers=headers)).status_code == 200
    assert (await cliente.get("/api/v1/reporteria/kpis", headers=headers)).status_code == 200

    crear_prod = await cliente.post(
        "/api/v1/productos",
        headers=headers,
        json={"sku": "V-1", "nombre": "No", "precio": 1, "stock": 0},
    )
    assert crear_prod.status_code == 403

    crear_cli = await cliente.post(
        "/api/v1/clientes",
        headers=headers,
        json={"nombre": "No", "email": "no@demo.com", "telefono": "1"},
    )
    assert crear_cli.status_code == 403

    compras = await cliente.post(
        "/api/v1/compras",
        headers=headers,
        json={
            "tipo": "factura_compra",
            "proveedor_id": "prov-x",
            "deposito_id": "dep-x",
            "lineas": [{"producto_id": "p", "cantidad": 1, "precio_unitario": 1}],
        },
    )
    assert compras.status_code == 403

    matriz = await cliente.get("/api/v1/tenants/permisos", headers=headers)
    assert matriz.status_code == 403


@pytest.mark.asyncio
async def test_encargado_articulos_si_clientes_no(cliente, auth_headers) -> None:
    await _reset_matriz(cliente, auth_headers)
    headers = await _alta_y_login(
        cliente, auth_headers, rol="encargado", email="enc-matriz@ventas360.com"
    )
    me = await cliente.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    permisos = set(me.json()["permisos"])
    assert "articulos" in permisos
    assert "stock" in permisos
    assert "clientes" not in permisos

    crear_prod = await cliente.post(
        "/api/v1/productos",
        headers=headers,
        json={"sku": "E-1", "nombre": "Sí", "precio": 10, "stock": 1},
    )
    assert crear_prod.status_code == 201, crear_prod.text

    crear_cli = await cliente.post(
        "/api/v1/clientes",
        headers=headers,
        json={"nombre": "No", "email": "enc-no@demo.com", "telefono": "1"},
    )
    assert crear_cli.status_code == 403


@pytest.mark.asyncio
async def test_admin_lee_y_edita_matriz(cliente, auth_headers) -> None:
    await _reset_matriz(cliente, auth_headers)
    get_matriz = await cliente.get("/api/v1/tenants/permisos", headers=auth_headers)
    assert get_matriz.status_code == 200, get_matriz.text
    items = get_matriz.json()["items"]
    por_mod = {i["modulo"]: i for i in items}
    assert por_mod["articulos"]["vendedor"] is False
    assert por_mod["articulos"]["encargado"] is True
    assert por_mod["articulos"]["administrador"] is True
    assert por_mod["inicio"]["vendedor"] is True

    put = await cliente.put(
        "/api/v1/tenants/permisos",
        headers=auth_headers,
        json={
            "rol": "vendedor",
            "modulos": {
                "inicio": True,
                "mostrador": True,
                "cta_cte": True,
                "articulos": True,
                "stock": False,
                "clientes": False,
                "ventas": False,
                "compras": False,
            },
        },
    )
    assert put.status_code == 200, put.text
    actualizado = {i["modulo"]: i for i in put.json()["items"]}
    assert actualizado["articulos"]["vendedor"] is True

    headers_v = await _alta_y_login(
        cliente, auth_headers, rol="vendedor", email="vend-art@ventas360.com"
    )
    crear_prod = await cliente.post(
        "/api/v1/productos",
        headers=headers_v,
        json={"sku": "V-ART", "nombre": "Con tilde", "precio": 1, "stock": 0},
    )
    assert crear_prod.status_code == 201, crear_prod.text

    rechazo_admin = await cliente.put(
        "/api/v1/tenants/permisos",
        headers=auth_headers,
        json={"rol": "administrador", "modulos": {"inicio": False}},
    )
    assert rechazo_admin.status_code == 422


@pytest.mark.asyncio
async def test_superadmin_no_ve_matriz_de_comercio(
    cliente, plataforma_headers
) -> None:
    en_plataforma = await cliente.get(
        "/api/v1/tenants/permisos",
        headers=plataforma_headers,
    )
    assert en_plataforma.status_code == 403

    en_demo = await cliente.get(
        "/api/v1/tenants/permisos",
        headers={"Authorization": plataforma_headers["Authorization"]},
    )
    assert en_demo.status_code == 403
