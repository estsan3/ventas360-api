"""API del módulo proveedores."""

import json
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import obtener_sesion
from app.core.dependencias import obtener_usuario_actual, requerir_rol
from app.core.excepciones import ReglaDeNegocioViolada
from app.modulos.proveedores.schemas import (
    ActualizarProveedorRequest,
    CrearProveedorRequest,
    ImportarListaResponse,
    ProveedorResponse,
    ProveedoresPaginaResponse,
)
from app.modulos.proveedores.service import ProveedoresService

router = APIRouter(
    prefix="/proveedores",
    tags=["Proveedores"],
    dependencies=[Depends(obtener_usuario_actual)],
)

Sesion = Annotated[AsyncSession, Depends(obtener_sesion)]


@router.get("", response_model=ProveedoresPaginaResponse, operation_id="listar_proveedores")
async def listar_proveedores(
    sesion: Sesion,
    q: str | None = Query(default=None),
    activo: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
) -> ProveedoresPaginaResponse:
    return await ProveedoresService(sesion).listar(
        q=q, activo=activo, page=page, page_size=page_size
    )


@router.get(
    "/{proveedor_id}",
    response_model=ProveedorResponse,
    operation_id="obtener_proveedor",
)
async def obtener_proveedor(proveedor_id: str, sesion: Sesion) -> ProveedorResponse:
    return await ProveedoresService(sesion).obtener(proveedor_id)


@router.post(
    "",
    response_model=ProveedorResponse,
    status_code=201,
    dependencies=[Depends(requerir_rol("administrador"))],
    operation_id="crear_proveedor",
)
async def crear_proveedor(
    datos: CrearProveedorRequest, sesion: Sesion
) -> ProveedorResponse:
    return await ProveedoresService(sesion).crear(datos)


@router.put(
    "/{proveedor_id}",
    response_model=ProveedorResponse,
    dependencies=[Depends(requerir_rol("administrador"))],
    operation_id="actualizar_proveedor",
)
async def actualizar_proveedor(
    proveedor_id: str, datos: ActualizarProveedorRequest, sesion: Sesion
) -> ProveedorResponse:
    return await ProveedoresService(sesion).actualizar(proveedor_id, datos)


@router.patch(
    "/{proveedor_id}/desactivar",
    response_model=ProveedorResponse,
    dependencies=[Depends(requerir_rol("administrador"))],
    operation_id="desactivar_proveedor",
)
async def desactivar_proveedor(proveedor_id: str, sesion: Sesion) -> ProveedorResponse:
    return await ProveedoresService(sesion).desactivar(proveedor_id)


@router.post(
    "/{proveedor_id}/listas/importar",
    response_model=ImportarListaResponse,
    dependencies=[Depends(requerir_rol("administrador"))],
    operation_id="importar_lista_proveedor",
)
async def importar_lista_proveedor(
    proveedor_id: str,
    sesion: Sesion,
    archivo: UploadFile = File(...),
    mapeo: str | None = Form(default=None),
    fila_inicio: int | None = Form(default=None),
    politica_precio_venta: str | None = Form(default=None),
    margen_venta_pct: float | None = Form(default=None),
    dry_run: bool = Query(default=False),
) -> ImportarListaResponse:
    """Importa (o previsualiza) una lista Excel → upsert de artículos/costos."""
    nombre = archivo.filename or "lista.xlsx"
    if not nombre.lower().endswith((".xlsx", ".xlsm")):
        raise ReglaDeNegocioViolada("El archivo debe ser Excel (.xlsx)")
    contenido = await archivo.read()
    if not contenido:
        raise ReglaDeNegocioViolada("El archivo está vacío")

    mapeo_override = None
    if mapeo:
        try:
            parsed = json.loads(mapeo)
        except json.JSONDecodeError as exc:
            raise ReglaDeNegocioViolada("mapeo debe ser JSON válido") from exc
        if not isinstance(parsed, list):
            raise ReglaDeNegocioViolada("mapeo debe ser una lista")
        mapeo_override = [
            {"columna": str(item.get("columna", "")), "campo": str(item.get("campo", ""))}
            for item in parsed
            if isinstance(item, dict)
        ]

    return await ProveedoresService(sesion).importar_lista(
        proveedor_id,
        contenido=contenido,
        nombre_archivo=nombre,
        mapeo_override=mapeo_override,
        fila_inicio=fila_inicio,
        politica=politica_precio_venta,
        margen_pct=margen_venta_pct,
        dry_run=dry_run,
    )
