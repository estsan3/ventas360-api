"""Dependencias de webhook n8n."""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import obtener_configuracion
from app.core.database import obtener_sesion
from app.core.excepciones import NoAutenticado
from app.core.tenant_ctx import usando_tenant
from app.modulos.tenants.service import TenantsService

Sesion = Annotated[AsyncSession, Depends(obtener_sesion)]


async def verificar_webhook_n8n(
    x_ventas360_webhook_secret: Annotated[str | None, Header()] = None,
) -> None:
    cfg = obtener_configuracion()
    secreto = cfg.n8n_webhook_secret.strip()
    if not secreto:
        raise NoAutenticado(
            "Webhook n8n no configurado (VENTAS360_N8N_WEBHOOK_SECRET)"
        )
    if not x_ventas360_webhook_secret or x_ventas360_webhook_secret != secreto:
        raise NoAutenticado("Secreto de webhook inválido")


async def fijar_tenant_por_slug(
    sesion: Sesion,
    x_tenant_slug: Annotated[str | None, Header()] = None,
) -> AsyncIterator[str]:
    slug = (x_tenant_slug or "").strip().lower()
    if not slug:
        raise NoAutenticado("Falta header X-Tenant-Slug (ej. demo)")
    tenant = await TenantsService(sesion).obtener_por_slug(slug)
    with usando_tenant(tenant.id):
        yield tenant.id
