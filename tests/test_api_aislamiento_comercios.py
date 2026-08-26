"""Aislamiento entre comercios: A no lista, no lee y no muta datos de B."""

from typing import Any, TypedDict
from uuid import uuid4

import pytest

from tests.conftest import PASSWORD_TEST


class SesionComercio(TypedDict):
    tenant_id: str
    slug: str
    email: str
    origin: str
    headers: dict[str, str]


def _ids(cuerpo: Any) -> set[str]:
    if isinstance(cuerpo, list):
        return {item["id"] for item in cuerpo}
    return {item["id"] for item in cuerpo.get("items", [])}


def _error_negocio(respuesta) -> dict:
    assert "error" in respuesta.json(), respuesta.text
    cuerpo = respuesta.json()["error"]
    assert "secreto" not in cuerpo["mensaje"].lower()
    return cuerpo


def _ausente(respuesta) -> None:
    """El recurso de otro comercio no existe en este tenant."""
    assert respuesta.status_code == 404, respuesta.text
    assert _error_negocio(respuesta)["codigo"] == "no_encontrado"


def _oculto(respuesta) -> None:
    """404 (recurso) o 422 (FK de otro tenant). No se filtra el nombre."""
    assert respuesta.status_code in (404, 422), respuesta.text
    assert _error_negocio(respuesta)["codigo"] in {"no_encontrado", "regla_violada"}


async def _abrir_comercio(cliente, plataforma_headers, marca: str) -> SesionComercio:
    sufijo = uuid4().hex[:8]
    payload = {
        "nombre": f"Comercio {marca} {sufijo}",
        "slug": f"{marca}-{sufijo}",
        "administrador": {
            "nombre": f"Admin {marca}",
            "dni": "30111222",
            "email": f"admin-{marca}-{sufijo}@iso.demo",
            "password": PASSWORD_TEST,
        },
    }
    alta = await cliente.post(
        "/api/v1/tenants", headers=plataforma_headers, json=payload
    )
    assert alta.status_code == 201, alta.text
    origin = f"http://{payload['slug']}.localhost:4201"
    login = await cliente.post(
        "/api/v1/auth/login",
        headers={"Origin": origin},
        json={"email": payload["administrador"]["email"], "password": PASSWORD_TEST},
    )
    assert login.status_code == 200, login.text
    return {
        "tenant_id": alta.json()["id"],
        "slug": payload["slug"],
        "email": payload["administrador"]["email"],
        "origin": origin,
        "headers": {
            "Authorization": f"Bearer {login.json()['access_token']}",
            "Origin": origin,
        },
    }


@pytest.fixture
async def dos_comercios(cliente, plataforma_headers) -> tuple[SesionComercio, SesionComercio]:
    norte = await _abrir_comercio(cliente, plataforma_headers, "norte")
    sur = await _abrir_comercio(cliente, plataforma_headers, "sur")
    return norte, sur


async def _sembrar_catalogo(cliente, sesion: SesionComercio, marca: str) -> dict[str, str]:
    sufijo = uuid4().hex[:6]
    cli = await cliente.post(
        "/api/v1/clientes",
        headers=sesion["headers"],
        json={
            "nombre": f"AAA-SECRETO-{marca}-{sufijo}",
            "email": f"secreto-{marca}-{sufijo}@iso.demo",
            "telefono": "1",
        },
    )
    assert cli.status_code == 201, cli.text
    prod = await cliente.post(
        "/api/v1/productos",
        headers=sesion["headers"],
        json={
            "sku": f"SEC-{marca}-{sufijo}",
            "nombre": f"Producto secreto {marca}",
            "precio": 100.0,
            "costo": 40.0,
            "stock": 20,
        },
    )
    assert prod.status_code == 201, prod.text
    prov = await cliente.post(
        "/api/v1/proveedores",
        headers=sesion["headers"],
        json={"nombre": f"Proveedor secreto {marca}", "cuit": "30711222334"},
    )
    assert prov.status_code == 201, prov.text
    zona = await cliente.post(
        "/api/v1/zonas",
        headers=sesion["headers"],
        json={"nombre": f"Zona secreta {marca}", "codigo": f"Z{marca[:3].upper()}"},
    )
    assert zona.status_code == 201, zona.text
    dep = await cliente.post(
        "/api/v1/stock/depositos",
        headers=sesion["headers"],
        json={"codigo": f"D{marca[:3].upper()}", "nombre": f"Depósito {marca}"},
    )
    assert dep.status_code == 201, dep.text
    lista = await cliente.post(
        "/api/v1/precios/listas",
        headers=sesion["headers"],
        json={"codigo": f"L{marca[:3].upper()}", "nombre": f"Lista {marca}"},
    )
    assert lista.status_code == 201, lista.text
    vend = await cliente.post(
        "/api/v1/usuarios",
        headers=sesion["headers"],
        json={
            "nombre": f"Vendedor {marca}",
            "dni": "28990112",
            "email": f"vend-{marca}-{sufijo}@iso.demo",
            "password": PASSWORD_TEST,
            "rol": "vendedor",
        },
    )
    assert vend.status_code == 201, vend.text
    ajuste = await cliente.post(
        "/api/v1/stock/ajustes",
        headers=sesion["headers"],
        json={
            "articulo_id": prod.json()["id"],
            "deposito_id": dep.json()["id"],
            "cantidad": 20,
        },
    )
    assert ajuste.status_code == 200, ajuste.text
    pedido = await cliente.post(
        "/api/v1/ventas/pedidos",
        headers=sesion["headers"],
        json={
            "tipo": "pedido",
            "cliente_id": cli.json()["id"],
            "lineas": [{"producto_id": prod.json()["id"], "cantidad": 1}],
        },
    )
    assert pedido.status_code == 201, pedido.text
    return {
        "cliente_id": cli.json()["id"],
        "cliente_email": cli.json()["email"],
        "producto_id": prod.json()["id"],
        "sku": prod.json()["sku"],
        "proveedor_id": prov.json()["id"],
        "zona_id": zona.json()["id"],
        "deposito_id": dep.json()["id"],
        "lista_id": lista.json()["id"],
        "usuario_id": vend.json()["id"],
        "pedido_id": pedido.json()["id"],
    }


@pytest.mark.asyncio
async def test_login_no_cruza_de_un_comercio_al_otro(
    cliente, plataforma_headers, dos_comercios
) -> None:
    norte, sur = dos_comercios
    cruzado = await cliente.post(
        "/api/v1/auth/login",
        headers={"Origin": norte["origin"]},
        json={"email": sur["email"], "password": PASSWORD_TEST},
    )
    assert cruzado.status_code == 401
    assert "no pertenece" in cruzado.json()["error"]["mensaje"].lower()

    token_sur_en_norte = await cliente.get(
        "/api/v1/clientes",
        headers={**sur["headers"], "Origin": norte["origin"]},
    )
    assert token_sur_en_norte.status_code == 403


@pytest.mark.asyncio
async def test_listados_no_incluyen_entidades_del_otro(
    cliente, plataforma_headers, dos_comercios
) -> None:
    norte, sur = dos_comercios
    ids_sur = await _sembrar_catalogo(cliente, sur, "sur")
    await _sembrar_catalogo(cliente, norte, "norte")

    casos = [
        ("/api/v1/clientes", {"q": ids_sur["cliente_email"]}, ids_sur["cliente_id"]),
        ("/api/v1/productos", {"q": ids_sur["sku"]}, ids_sur["producto_id"]),
        ("/api/v1/proveedores", {"q": "secreto sur"}, ids_sur["proveedor_id"]),
        ("/api/v1/zonas", {"q": "secreta sur"}, ids_sur["zona_id"]),
        ("/api/v1/stock/depositos", None, ids_sur["deposito_id"]),
        ("/api/v1/precios/listas", None, ids_sur["lista_id"]),
        ("/api/v1/usuarios", None, ids_sur["usuario_id"]),
        ("/api/v1/catalogos/vendedores", None, ids_sur["usuario_id"]),
        ("/api/v1/ventas/pedidos", None, ids_sur["pedido_id"]),
    ]
    for ruta, params, ajeno in casos:
        lista = await cliente.get(ruta, headers=norte["headers"], params=params)
        assert lista.status_code == 200, f"{ruta}: {lista.text}"
        assert ajeno not in _ids(lista.json()), f"{ruta} filtró el id de Sur"


@pytest.mark.asyncio
async def test_get_y_mutacion_de_otro_comercio_estan_ocultos(
    cliente, plataforma_headers, dos_comercios
) -> None:
    norte, sur = dos_comercios
    ids = await _sembrar_catalogo(cliente, sur, "sur")
    h = norte["headers"]

    lecturas_404 = [
        f"/api/v1/clientes/{ids['cliente_id']}",
        f"/api/v1/productos/{ids['producto_id']}",
        f"/api/v1/proveedores/{ids['proveedor_id']}",
        f"/api/v1/zonas/{ids['zona_id']}",
        f"/api/v1/precios/listas/{ids['lista_id']}/articulos",
        f"/api/v1/ventas/pedidos/{ids['pedido_id']}",
        f"/api/v1/stock/articulos/{ids['producto_id']}/saldos",
        f"/api/v1/stock/depositos/{ids['deposito_id']}/inventario",
    ]
    for ruta in lecturas_404:
        _ausente(await cliente.get(ruta, headers=h))

    for ruta in (
        f"/api/v1/cxc/clientes/{ids['cliente_id']}/saldo",
        f"/api/v1/cxc/clientes/{ids['cliente_id']}/estado-cuenta",
    ):
        _oculto(await cliente.get(ruta, headers=h))

    mutaciones = [
        ("put", f"/api/v1/clientes/{ids['cliente_id']}", {"nombre": "Hack"}),
        ("patch", f"/api/v1/clientes/{ids['cliente_id']}/desactivar", None),
        ("put", f"/api/v1/productos/{ids['producto_id']}", {"nombre": "Hack"}),
        ("put", f"/api/v1/proveedores/{ids['proveedor_id']}", {"nombre": "Hack"}),
        ("patch", f"/api/v1/proveedores/{ids['proveedor_id']}/desactivar", None),
        ("put", f"/api/v1/zonas/{ids['zona_id']}", {"nombre": "Hack"}),
        ("put", f"/api/v1/stock/depositos/{ids['deposito_id']}", {"nombre": "Hack"}),
        ("patch", f"/api/v1/stock/depositos/{ids['deposito_id']}/desactivar", None),
        ("put", f"/api/v1/precios/listas/{ids['lista_id']}", {"nombre": "Hack"}),
        ("patch", f"/api/v1/ventas/pedidos/{ids['pedido_id']}/estado", {"estado": "confirmado"}),
        ("post", f"/api/v1/ventas/pedidos/{ids['pedido_id']}/confirmar-remito", None),
        ("delete", f"/api/v1/usuarios/{ids['usuario_id']}", None),
    ]
    for metodo, ruta, cuerpo in mutaciones:
        kwargs: dict = {"headers": h}
        if cuerpo is not None:
            kwargs["json"] = cuerpo
        respuesta = await getattr(cliente, metodo)(ruta, **kwargs)
        _ausente(respuesta)


@pytest.mark.asyncio
async def test_no_se_vende_ni_ajusta_con_ids_del_otro(
    cliente, plataforma_headers, dos_comercios
) -> None:
    norte, sur = dos_comercios
    ids_sur = await _sembrar_catalogo(cliente, sur, "sur")
    ids_norte = await _sembrar_catalogo(cliente, norte, "norte")
    h = norte["headers"]

    venta_cliente_ajeno = await cliente.post(
        "/api/v1/ventas/pedidos",
        headers=h,
        json={
            "tipo": "pedido",
            "cliente_id": ids_sur["cliente_id"],
            "lineas": [{"producto_id": ids_norte["producto_id"], "cantidad": 1}],
        },
    )
    _oculto(venta_cliente_ajeno)

    venta_producto_ajeno = await cliente.post(
        "/api/v1/ventas/pedidos",
        headers=h,
        json={
            "tipo": "pedido",
            "cliente_id": ids_norte["cliente_id"],
            "lineas": [{"producto_id": ids_sur["producto_id"], "cantidad": 1}],
        },
    )
    _oculto(venta_producto_ajeno)

    ajuste = await cliente.post(
        "/api/v1/stock/ajustes",
        headers=h,
        json={
            "articulo_id": ids_sur["producto_id"],
            "deposito_id": ids_norte["deposito_id"],
            "cantidad": 5,
        },
    )
    _oculto(ajuste)

    cxc = await cliente.post(
        "/api/v1/cxc/ajustes",
        headers=h,
        json={
            "cliente_id": ids_sur["cliente_id"],
            "tipo": "debe",
            "monto": 10,
            "concepto": "Hack",
        },
    )
    _oculto(cxc)


@pytest.mark.asyncio
async def test_parametros_y_kpis_no_mezclan_comercios(
    cliente, plataforma_headers, dos_comercios
) -> None:
    norte, sur = dos_comercios
    await _sembrar_catalogo(cliente, sur, "sur")
    await _sembrar_catalogo(cliente, norte, "norte")

    iva_sur = await cliente.put(
        "/api/v1/parametros",
        headers=sur["headers"],
        json={"iva_porcentaje": 10.5, "moneda": "ARS"},
    )
    assert iva_sur.status_code == 200, iva_sur.text
    iva_norte = await cliente.put(
        "/api/v1/parametros",
        headers=norte["headers"],
        json={"iva_porcentaje": 21.0, "moneda": "USD"},
    )
    assert iva_norte.status_code == 200, iva_norte.text

    leido_sur = await cliente.get("/api/v1/parametros", headers=sur["headers"])
    leido_norte = await cliente.get("/api/v1/parametros", headers=norte["headers"])
    assert leido_sur.json()["iva_porcentaje"] == 10.5
    assert leido_sur.json()["moneda"] == "ARS"
    assert leido_norte.json()["iva_porcentaje"] == 21.0
    assert leido_norte.json()["moneda"] == "USD"

    extra_sur = await cliente.post(
        "/api/v1/clientes",
        headers=sur["headers"],
        json={"nombre": "Extra Sur", "email": f"extra-{uuid4().hex[:6]}@sur.demo", "telefono": "1"},
    )
    assert extra_sur.status_code == 201, extra_sur.text

    kpis_norte = await cliente.get("/api/v1/reporteria/kpis", headers=norte["headers"])
    kpis_sur = await cliente.get("/api/v1/reporteria/kpis", headers=sur["headers"])
    assert kpis_norte.status_code == 200 and kpis_sur.status_code == 200
    assert kpis_sur.json()["clientes_activos"] == kpis_norte.json()["clientes_activos"] + 1
    assert kpis_norte.json()["productos_activos"] == 1
    assert kpis_sur.json()["productos_activos"] == 1

    saldos_norte = await cliente.get("/api/v1/cxc/saldos", headers=norte["headers"])
    assert saldos_norte.status_code == 200
    ids_saldos = {item["cliente_id"] for item in saldos_norte.json()}
    ids_sur = await cliente.get("/api/v1/clientes", headers=sur["headers"])
    for cliente_sur in _ids(ids_sur.json()):
        assert cliente_sur not in ids_saldos


@pytest.mark.asyncio
async def test_comercio_ve_sus_propios_datos(
    cliente, plataforma_headers, dos_comercios
) -> None:
    norte, sur = dos_comercios
    ids = await _sembrar_catalogo(cliente, sur, "sur")
    propio = await cliente.get(
        f"/api/v1/clientes/{ids['cliente_id']}", headers=sur["headers"]
    )
    assert propio.status_code == 200
    assert propio.json()["id"] == ids["cliente_id"]
    pedido = await cliente.get(
        f"/api/v1/ventas/pedidos/{ids['pedido_id']}", headers=sur["headers"]
    )
    assert pedido.status_code == 200


@pytest.mark.asyncio
async def test_token_demo_no_usa_origin_de_otro_comercio(
    cliente, plataforma_headers, auth_headers, dos_comercios
) -> None:
    _, sur = dos_comercios
    respuesta = await cliente.get(
        "/api/v1/clientes",
        headers={**auth_headers, "Origin": sur["origin"]},
    )
    assert respuesta.status_code == 403
    assert respuesta.json()["error"]["codigo"] == "no_autorizado"
