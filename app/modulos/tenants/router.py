"""API del módulo tenants: contexto público + CRUD de plataforma."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import obtener_sesion
from app.core.dependencias import requerir_rol
from app.modulos.tenants.dependencias import (
    exigir_host_plataforma,
    exigir_usuario_del_comercio,
    requerir_modulo,
)
from app.modulos.tenants.host import hostname_desde_request
from app.modulos.tenants.schemas import (
    ActualizarPermisosRequest,
    ActualizarTenantRequest,
    ContextoHostResponse,
    CrearTenantRequest,
    MatrizPermisosResponse,
    TenantCreadoResponse,
    TenantResponse,
)
from app.modulos.tenants.service import TenantsService

router = APIRouter(prefix="/tenants", tags=["Tenants"])

router_plataforma = APIRouter(
    prefix="/tenants",
    tags=["Tenants"],
    dependencies=[
        Depends(exigir_host_plataforma),
        Depends(requerir_rol("superadmin")),
    ],
)

router_comercio = APIRouter(
    prefix="/tenants",
    tags=["Tenants"],
    dependencies=[
        Depends(exigir_usuario_del_comercio),
        Depends(requerir_modulo("configuracion")),
    ],
)

Sesion = Annotated[AsyncSession, Depends(obtener_sesion)]


@router.get(
    "/contexto",
    response_model=ContextoHostResponse,
    operation_id="contexto_tenant_host",
)
async def contexto_tenant_host(request: Request, sesion: Sesion) -> ContextoHostResponse:
    """Resuelve plataforma vs comercio según Origin / X-Forwarded-Host / Host."""
    host = hostname_desde_request(request)
    return await TenantsService(sesion).contexto_desde_host(host)


@router_plataforma.get(
    "",
    response_model=list[TenantResponse],
    operation_id="listar_tenants",
)
async def listar_tenants(sesion: Sesion) -> list[TenantResponse]:
    """Lista comercios (incluye inactivos). Solo superadmin en admin.*."""
    return await TenantsService(sesion).listar()


@router_plataforma.post(
    "",
    response_model=TenantCreadoResponse,
    status_code=201,
    operation_id="crear_tenant",
)
async def crear_tenant(
    datos: CrearTenantRequest, sesion: Sesion
) -> TenantCreadoResponse:
    """Alta de comercio y primer administrador. El slug no se cambia después."""
    return await TenantsService(sesion).crear(datos)


@router_plataforma.get(
    "/{tenant_id}",
    response_model=TenantResponse,
    operation_id="obtener_tenant",
)
async def obtener_tenant(tenant_id: str, sesion: Sesion) -> TenantResponse:
    return await TenantsService(sesion).obtener(tenant_id)


@router_plataforma.patch(
    "/{tenant_id}",
    response_model=TenantResponse,
    operation_id="actualizar_tenant",
)
async def actualizar_tenant(
    tenant_id: str, datos: ActualizarTenantRequest, sesion: Sesion
) -> TenantResponse:
    """Edita nombre comercial o activo. El slug es de solo lectura."""
    return await TenantsService(sesion).actualizar(tenant_id, datos)


@router_comercio.get(
    "/permisos",
    response_model=MatrizPermisosResponse,
    operation_id="obtener_matriz_permisos",
)
async def obtener_matriz_permisos(sesion: Sesion) -> MatrizPermisosResponse:
    """Matriz módulo × rol. El administrador no se edita."""
    return await TenantsService(sesion).obtener_matriz()


@router_comercio.put(
    "/permisos",
    response_model=MatrizPermisosResponse,
    operation_id="actualizar_matriz_permisos",
)
async def actualizar_matriz_permisos(
    datos: ActualizarPermisosRequest, sesion: Sesion
) -> MatrizPermisosResponse:
    """Edita tildes de Vendedor o Encargado."""
    return await TenantsService(sesion).actualizar_permisos(datos)
