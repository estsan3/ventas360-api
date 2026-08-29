"""API del módulo compras."""

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import obtener_sesion
from app.modulos.compras.schemas import (
    CompraResponse,
    CrearCompraRequest,
    ParsearRemitoResponse,
)
from app.modulos.compras.service import ComprasService
from app.modulos.tenants.dependencias import exigir_usuario_del_comercio, requerir_modulo

router = APIRouter(
    prefix="/compras",
    tags=["Compras"],
    dependencies=[
        Depends(exigir_usuario_del_comercio),
        Depends(requerir_modulo("compras")),
    ],
)

Sesion = Annotated[AsyncSession, Depends(obtener_sesion)]


@router.get("", response_model=list[CompraResponse], operation_id="listar_compras")
async def listar_compras(
    sesion: Sesion,
    tipo: str | None = Query(default=None),
) -> list[CompraResponse]:
    return await ComprasService(sesion).listar(tipo=tipo)


@router.post(
    "/remitos/parsear",
    response_model=ParsearRemitoResponse,
    operation_id="parsear_remito_foto",
)
async def parsear_remito_foto(
    sesion: Sesion,
    archivo: UploadFile = File(..., description="Foto del remito (JPEG, PNG o WebP)"),
    proveedor_id: str | None = Form(default=None),
    deposito_id: str | None = Form(default=None),
) -> ParsearRemitoResponse:
    contenido = await archivo.read()
    return await ComprasService(sesion).parsear_remito_foto(
        contenido=contenido,
        nombre_archivo=archivo.filename,
        content_type=archivo.content_type,
        proveedor_id=proveedor_id,
        deposito_id=deposito_id,
    )


@router.get("/{compra_id}", response_model=CompraResponse, operation_id="obtener_compra")
async def obtener_compra(compra_id: str, sesion: Sesion) -> CompraResponse:
    return await ComprasService(sesion).obtener(compra_id)


@router.post(
    "",
    response_model=CompraResponse,
    status_code=201,
    operation_id="crear_compra",
)
async def crear_compra(datos: CrearCompraRequest, sesion: Sesion) -> CompraResponse:
    return await ComprasService(sesion).crear(datos)


@router.post(
    "/{compra_id}/confirmar",
    response_model=CompraResponse,
    operation_id="confirmar_compra",
)
async def confirmar_compra(compra_id: str, sesion: Sesion) -> CompraResponse:
    return await ComprasService(sesion).confirmar(compra_id)


@router.post(
    "/{compra_id}/emitir",
    response_model=CompraResponse,
    operation_id="emitir_pedido_compra",
)
async def emitir_pedido_compra(compra_id: str, sesion: Sesion) -> CompraResponse:
    return await ComprasService(sesion).emitir(compra_id)


@router.post(
    "/{compra_id}/facturar",
    response_model=CompraResponse,
    operation_id="facturar_remito_compra",
)
async def facturar_remito_compra(compra_id: str, sesion: Sesion) -> CompraResponse:
    return await ComprasService(sesion).facturar_remito(compra_id)
