"""Dependencias HTTP de tenants: comercio del Host vs plataforma."""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import obtener_sesion
from app.core.dependencias import UsuarioActual, obtener_usuario_actual
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


async def exigir_usuario_del_comercio(
    request: Request,
    sesion: Sesion,
    usuario: Annotated[UsuarioActual, Depends(obtener_usuario_actual)],
) -> AsyncIterator[str]:
    """Comercio del Host + el JWT debe ser de ese mismo comercio."""
    async for tenant_id in fijar_tenant_de_host(request, sesion):
        if usuario.tenant_id != tenant_id:
            raise NoAutorizado("El usuario no pertenece a este comercio")
        yield tenant_id


def requerir_modulo(*modulos: str):
    """Exige que el rol tenga al menos uno de los módulos indicados."""

    async def _verificar(
        usuario: Annotated[UsuarioActual, Depends(obtener_usuario_actual)],
        sesion: Sesion,
    ) -> UsuarioActual:
        tenant_id = usuario.tenant_id
        if not tenant_id:
            raise NoAutorizado("Esta operación es de un comercio")
        habilitados = set(
            await TenantsService(sesion).modulos_habilitados(tenant_id, usuario.rol)
        )
        if not habilitados.intersection(modulos):
            raise NoAutorizado("No tenés acceso a este módulo")
        return usuario

    return _verificar
