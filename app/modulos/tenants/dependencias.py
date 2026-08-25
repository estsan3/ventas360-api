"""Dependencias HTTP de tenants: comercio del Host vs plataforma."""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import obtener_sesion
from app.core.excepciones import NoAutorizado, RecursoNoEncontrado
from app.core.tenant_ctx import usando_tenant
from app.modulos.tenants.host import hostname_desde_request
from app.modulos.tenants.service import TenantsService

Sesion = Annotated[AsyncSession, Depends(obtener_sesion)]


async def fijar_tenant_de_host(
    request: Request, sesion: Sesion
) -> AsyncIterator[str]:
    """Exige un subdominio de comercio existente y activo."""
    host = hostname_desde_request(request)
    ctx = await TenantsService(sesion).contexto_desde_host(host)
    if ctx.tipo == "plataforma":
        raise NoAutorizado("Esta operación es de un comercio, no de la plataforma")
    if ctx.tenant is None:
        raise RecursoNoEncontrado(
            "No hay un comercio para este subdominio. "
            "Entrá con el slug (ej. agronorte.localhost:4201)."
        )
    with usando_tenant(ctx.tenant.id):
        yield ctx.tenant.id


async def exigir_host_plataforma(request: Request, sesion: Sesion) -> None:
    """Exige el host de plataforma (`admin.*`)."""
    host = hostname_desde_request(request)
    ctx = await TenantsService(sesion).contexto_desde_host(host)
    if ctx.tipo != "plataforma":
        raise NoAutorizado(
            "Esta operación es de la plataforma (admin), no de un comercio"
        )
