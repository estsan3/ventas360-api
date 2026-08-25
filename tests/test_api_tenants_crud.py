"""CRUD de comercios: solo superadmin en admin.*."""

import uuid

import pytest

from app.core.database import fabrica_sesiones
from app.modulos.auth.dao import UsuarioDAO
from app.modulos.tenants.ids import ID_TENANT_DEMO, SLUG_TENANT_DEMO
from tests.conftest import ORIGIN_DEMO, ORIGIN_PLATAFORMA


def _alta(*, slug: str | None = None, email: str | None = None) -> dict:
    sufijo = uuid.uuid4().hex[:8]
    return {
        "nombre": "Kiosco Milka",
        "slug": slug or f"milka-{sufijo}",
        "administrador": {
            "nombre": "Ana Milka",
            "dni": "30111222",
            "email": email or f"ana-{sufijo}@milka.demo",
            "password": "demo12345",
        },
    }


@pytest.mark.asyncio
async def test_superadmin_crea_comercio_con_primer_admin(
    cliente, plataforma_headers
) -> None:
    payload = _alta(slug="kiosco-milka")
    respuesta = await cliente.post(
        "/api/v1/tenants",
        headers=plataforma_headers,
        json=payload,
    )
    assert respuesta.status_code == 201, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["slug"] == "kiosco-milka"
    assert cuerpo["nombre"] == "Kiosco Milka"
    assert cuerpo["activo"] is True
    assert cuerpo["administrador"]["email"] == payload["administrador"]["email"]
    assert cuerpo["administrador"]["rol"] == "administrador"
    assert "password" not in cuerpo["administrador"]

    async with fabrica_sesiones() as sesion:
        admin = await UsuarioDAO(sesion).buscar_por_email(
            payload["administrador"]["email"]
        )
        assert admin is not None
        assert admin.tenant_id == cuerpo["id"]
        assert admin.rol == "administrador"

    login = await cliente.post(
        "/api/v1/auth/login",
        headers={"Origin": "http://kiosco-milka.localhost:4201"},
        json={
            "email": payload["administrador"]["email"],
            "password": "demo12345",
        },
    )
    assert login.status_code == 200
    assert login.json()["usuario"]["rol"] == "administrador"


@pytest.mark.asyncio
async def test_listar_tenants_incluye_demo_y_alta(
    cliente, plataforma_headers
) -> None:
    payload = _alta()
    alta = await cliente.post(
        "/api/v1/tenants", headers=plataforma_headers, json=payload
    )
    assert alta.status_code == 201, alta.text

    lista = await cliente.get("/api/v1/tenants", headers=plataforma_headers)
    assert lista.status_code == 200
    slugs = {t["slug"] for t in lista.json()}
    assert SLUG_TENANT_DEMO in slugs
    assert payload["slug"] in slugs


@pytest.mark.asyncio
async def test_obtener_y_actualizar_nombre(cliente, plataforma_headers) -> None:
    creado = await cliente.post(
        "/api/v1/tenants", headers=plataforma_headers, json=_alta()
    )
    assert creado.status_code == 201, creado.text
    tenant_id = creado.json()["id"]
    slug = creado.json()["slug"]

    detalle = await cliente.get(
        f"/api/v1/tenants/{tenant_id}", headers=plataforma_headers
    )
    assert detalle.status_code == 200
    assert detalle.json()["slug"] == slug

    patch = await cliente.patch(
        f"/api/v1/tenants/{tenant_id}",
        headers=plataforma_headers,
        json={"nombre": "Kiosco Milka Centro"},
    )
    assert patch.status_code == 200
    assert patch.json()["nombre"] == "Kiosco Milka Centro"
    assert patch.json()["slug"] == slug


@pytest.mark.asyncio
async def test_desactivar_oculta_comercio_en_contexto(
    cliente, plataforma_headers
) -> None:
    payload = _alta()
    creado = await cliente.post(
        "/api/v1/tenants", headers=plataforma_headers, json=payload
    )
    assert creado.status_code == 201, creado.text
    tenant_id = creado.json()["id"]
    slug = payload["slug"]

    baja = await cliente.patch(
        f"/api/v1/tenants/{tenant_id}",
        headers=plataforma_headers,
        json={"activo": False},
    )
    assert baja.status_code == 200
    assert baja.json()["activo"] is False

    ctx = await cliente.get(
        "/api/v1/tenants/contexto",
        headers={"Origin": f"http://{slug}.localhost:4201"},
    )
    assert ctx.status_code == 200
    assert ctx.json()["tipo"] == "comercio"
    assert ctx.json()["tenant"] is None


@pytest.mark.asyncio
async def test_slug_duplicado_y_reservado(cliente, plataforma_headers) -> None:
    payload = _alta()
    primero = await cliente.post(
        "/api/v1/tenants", headers=plataforma_headers, json=payload
    )
    assert primero.status_code == 201, primero.text

    duplicado = await cliente.post(
        "/api/v1/tenants", headers=plataforma_headers, json=payload
    )
    assert duplicado.status_code == 422
    assert "slug" in duplicado.json()["error"]["mensaje"].lower()

    reservado = await cliente.post(
        "/api/v1/tenants",
        headers=plataforma_headers,
        json=_alta(slug="admin"),
    )
    assert reservado.status_code == 422
    assert "reservado" in reservado.json()["error"]["mensaje"].lower()


@pytest.mark.asyncio
async def test_email_admin_duplicado_global(cliente, plataforma_headers) -> None:
    email = f"ana-dup-{uuid.uuid4().hex[:8]}@milka.demo"
    primero = await cliente.post(
        "/api/v1/tenants",
        headers=plataforma_headers,
        json=_alta(email=email),
    )
    assert primero.status_code == 201, primero.text

    otro = await cliente.post(
        "/api/v1/tenants",
        headers=plataforma_headers,
        json=_alta(email=email),
    )
    assert otro.status_code == 422
    assert "email" in otro.json()["error"]["mensaje"].lower()


@pytest.mark.asyncio
async def test_admin_de_comercio_no_puede_crear_tenant(
    cliente, auth_headers
) -> None:
    respuesta = await cliente.post(
        "/api/v1/tenants",
        headers={**auth_headers, "Origin": ORIGIN_PLATAFORMA},
        json=_alta(),
    )
    assert respuesta.status_code == 403


@pytest.mark.asyncio
async def test_superadmin_desde_comercio_no_puede_crear(
    cliente, plataforma_headers
) -> None:
    respuesta = await cliente.post(
        "/api/v1/tenants",
        headers={
            "Authorization": plataforma_headers["Authorization"],
            "Origin": ORIGIN_DEMO,
        },
        json=_alta(),
    )
    assert respuesta.status_code == 403


@pytest.mark.asyncio
async def test_sin_token_es_401(cliente) -> None:
    respuesta = await cliente.get(
        "/api/v1/tenants",
        headers={"Origin": ORIGIN_PLATAFORMA},
    )
    assert respuesta.status_code == 401


@pytest.mark.asyncio
async def test_obtener_inexistente_es_404(cliente, plataforma_headers) -> None:
    respuesta = await cliente.get(
        f"/api/v1/tenants/{ID_TENANT_DEMO}-no-existe",
        headers=plataforma_headers,
    )
    assert respuesta.status_code == 404
    assert respuesta.json()["error"]["codigo"] == "no_encontrado"
