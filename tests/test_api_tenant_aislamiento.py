"""Aislamiento: un comercio no ve datos de otro (404, no 403)."""

import pytest

from app.core.database import fabrica_sesiones
from app.core.seguridad import hashear_password
from app.core.tenant_ctx import usando_tenant
from app.modulos.auth.models import Usuario
from app.modulos.clientes.models import Cliente
from app.modulos.productos.models import Producto
from app.modulos.tenants.models import Tenant

ID_MILKA = "tnt-milka-aislamiento"
ID_CLIENTE_MILKA = "cli-secreto-milka"
ID_PRODUCTO_MILKA = "prd-secreto-milka"
ID_USUARIO_MILKA = "usr-admin-milka"


async def _sembrar_comercio_milka() -> None:
    async with fabrica_sesiones() as sesion:
        if await sesion.get(Tenant, ID_MILKA) is None:
            sesion.add(
                Tenant(id=ID_MILKA, slug="milka-iso", nombre="Kiosco Milka")
            )
        with usando_tenant(ID_MILKA):
            if await sesion.get(Cliente, ID_CLIENTE_MILKA) is None:
                sesion.add(
                    Cliente(
                        id=ID_CLIENTE_MILKA,
                        tenant_id=ID_MILKA,
                        nombre="Cliente secreto Milka",
                        email="secreto@milka.demo",
                    )
                )
            if await sesion.get(Producto, ID_PRODUCTO_MILKA) is None:
                sesion.add(
                    Producto(
                        id=ID_PRODUCTO_MILKA,
                        tenant_id=ID_MILKA,
                        sku="MILKA-X",
                        nombre="Producto secreto",
                        precio=10.0,
                    )
                )
            if await sesion.get(Usuario, ID_USUARIO_MILKA) is None:
                sesion.add(
                    Usuario(
                        id=ID_USUARIO_MILKA,
                        tenant_id=ID_MILKA,
                        nombre="Admin Milka",
                        dni="22222222",
                        email="admin@milka-iso.demo",
                        password_hash=hashear_password("demo12345"),
                        rol="administrador",
                    )
                )
            await sesion.commit()


@pytest.mark.asyncio
async def test_listado_no_incluye_cliente_de_otro_comercio(
    cliente, auth_headers
) -> None:
    await _sembrar_comercio_milka()

    propio = await cliente.post(
        "/api/v1/clientes",
        headers=auth_headers,
        json={
            "nombre": "Cliente Demo",
            "email": "propio-iso@demo.com",
            "telefono": "1",
        },
    )
    assert propio.status_code == 201, propio.text
    propio_id = propio.json()["id"]

    pagina_ajena = await cliente.get(
        "/api/v1/clientes",
        headers=auth_headers,
        params={"q": "secreto@milka"},
    )
    assert pagina_ajena.status_code == 200
    assert pagina_ajena.json()["total"] == 0
    assert ID_CLIENTE_MILKA not in [item["id"] for item in pagina_ajena.json()["items"]]

    pagina_propia = await cliente.get(
        "/api/v1/clientes",
        headers=auth_headers,
        params={"q": "propio-iso@demo.com"},
    )
    assert pagina_propia.status_code == 200
    ids = [item["id"] for item in pagina_propia.json()["items"]]
    assert propio_id in ids


@pytest.mark.asyncio
async def test_get_cliente_ajeno_es_404_sin_filtrar_existencia(
    cliente, auth_headers
) -> None:
    await _sembrar_comercio_milka()

    respuesta = await cliente.get(
        f"/api/v1/clientes/{ID_CLIENTE_MILKA}",
        headers=auth_headers,
    )
    assert respuesta.status_code == 404
    cuerpo = respuesta.json()
    assert cuerpo["error"]["codigo"] == "no_encontrado"
    assert "Milka" not in cuerpo["error"]["mensaje"]


@pytest.mark.asyncio
async def test_get_producto_ajeno_es_404(cliente, auth_headers) -> None:
    await _sembrar_comercio_milka()

    respuesta = await cliente.get(
        f"/api/v1/productos/{ID_PRODUCTO_MILKA}",
        headers=auth_headers,
    )
    assert respuesta.status_code == 404
    assert respuesta.json()["error"]["codigo"] == "no_encontrado"


@pytest.mark.asyncio
async def test_listado_usuarios_no_incluye_admin_de_otro_comercio(
    cliente, auth_headers
) -> None:
    await _sembrar_comercio_milka()

    lista = await cliente.get("/api/v1/usuarios", headers=auth_headers)
    assert lista.status_code == 200
    ids = [u["id"] for u in lista.json()]
    assert ID_USUARIO_MILKA not in ids


@pytest.mark.asyncio
async def test_eliminar_usuario_ajeno_es_404(cliente, auth_headers) -> None:
    await _sembrar_comercio_milka()

    respuesta = await cliente.delete(
        f"/api/v1/usuarios/{ID_USUARIO_MILKA}",
        headers=auth_headers,
    )
    assert respuesta.status_code == 404
    assert respuesta.json()["error"]["codigo"] == "no_encontrado"
