"""Service del módulo proveedores."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.excepciones import RecursoNoEncontrado
from app.modulos.proveedores.bo import ProveedorBO
from app.modulos.proveedores.dao import ProveedorDAO
from app.modulos.proveedores.models import Proveedor
from app.modulos.proveedores.schemas import (
    ActualizarProveedorRequest,
    CrearProveedorRequest,
    ProveedorResponse,
    ProveedoresPaginaResponse,
)


class ProveedoresService:
    def __init__(self, sesion: AsyncSession) -> None:
        self._sesion = sesion
        self._dao = ProveedorDAO(sesion)
        self._bo = ProveedorBO()

    async def listar(
        self,
        *,
        q: str | None = None,
        activo: bool | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> ProveedoresPaginaResponse:
        items, total = await self._dao.listar(
            q=q, activo=activo, page=page, page_size=page_size
        )
        return ProveedoresPaginaResponse(
            items=[ProveedorResponse.model_validate(p) for p in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def obtener(self, proveedor_id: str) -> ProveedorResponse:
        return ProveedorResponse.model_validate(await self._buscar_o_fallar(proveedor_id))

    async def crear(self, datos: CrearProveedorRequest) -> ProveedorResponse:
        self._bo.validar_datos(datos.cuit, datos.condicion_iva, datos.nombre)
        proveedor = Proveedor(
            nombre=datos.nombre.strip(),
            email=str(datos.email or ""),
            telefono=datos.telefono,
            cuit=datos.cuit.replace("-", "").strip(),
            condicion_iva=datos.condicion_iva,
            observaciones=datos.observaciones,
        )
        await self._dao.guardar(proveedor)
        await self._sesion.commit()
        return ProveedorResponse.model_validate(proveedor)

    async def actualizar(
        self, proveedor_id: str, datos: ActualizarProveedorRequest
    ) -> ProveedorResponse:
        proveedor = await self._buscar_o_fallar(proveedor_id)
        if datos.nombre is not None:
            proveedor.nombre = datos.nombre.strip()
        if datos.email is not None:
            proveedor.email = str(datos.email)
        if datos.telefono is not None:
            proveedor.telefono = datos.telefono
        if datos.cuit is not None:
            proveedor.cuit = datos.cuit.replace("-", "").strip()
        if datos.condicion_iva is not None:
            proveedor.condicion_iva = datos.condicion_iva
        if datos.observaciones is not None:
            proveedor.observaciones = datos.observaciones
        self._bo.validar_datos(
            proveedor.cuit, proveedor.condicion_iva, proveedor.nombre
        )
        await self._dao.guardar(proveedor)
        await self._sesion.commit()
        return ProveedorResponse.model_validate(proveedor)

    async def desactivar(self, proveedor_id: str) -> ProveedorResponse:
        proveedor = await self._buscar_o_fallar(proveedor_id)
        self._bo.validar_baja(proveedor.activo)
        proveedor.activo = False
        await self._dao.guardar(proveedor)
        await self._sesion.commit()
        return ProveedorResponse.model_validate(proveedor)

    async def _buscar_o_fallar(self, proveedor_id: str) -> Proveedor:
        proveedor = await self._dao.buscar_por_id(proveedor_id)
        if proveedor is None:
            raise RecursoNoEncontrado("Proveedor no encontrado")
        return proveedor
