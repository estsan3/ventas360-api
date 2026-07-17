"""Service del módulo zonas."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.excepciones import RecursoNoEncontrado, ReglaDeNegocioViolada
from app.modulos.zonas.bo import ZonaBO
from app.modulos.zonas.dao import ZonaDAO
from app.modulos.zonas.models import Zona
from app.modulos.zonas.schemas import (
    ActualizarZonaRequest,
    CrearZonaRequest,
    ZonaResponse,
    ZonasPaginaResponse,
)


class ZonasService:
    def __init__(self, sesion: AsyncSession) -> None:
        self._sesion = sesion
        self._dao = ZonaDAO(sesion)
        self._bo = ZonaBO()

    async def listar(
        self,
        *,
        q: str | None = None,
        activo: bool | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> ZonasPaginaResponse:
        items, total = await self._dao.listar(
            q=q, activo=activo, page=page, page_size=page_size
        )
        return ZonasPaginaResponse(
            items=[ZonaResponse.model_validate(z) for z in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def obtener(self, zona_id: str) -> ZonaResponse:
        return ZonaResponse.model_validate(await self._buscar_o_fallar(zona_id))

    async def crear(self, datos: CrearZonaRequest) -> ZonaResponse:
        self._bo.validar_nombre(datos.nombre)
        if await self._dao.buscar_por_nombre(datos.nombre):
            raise ReglaDeNegocioViolada("Ya existe una zona con ese nombre")
        zona = Zona(
            nombre=datos.nombre.strip(),
            codigo=datos.codigo.strip().upper(),
        )
        await self._dao.guardar(zona)
        await self._sesion.commit()
        return ZonaResponse.model_validate(zona)

    async def actualizar(
        self, zona_id: str, datos: ActualizarZonaRequest
    ) -> ZonaResponse:
        zona = await self._buscar_o_fallar(zona_id)
        if datos.nombre is not None:
            self._bo.validar_nombre(datos.nombre)
            otra = await self._dao.buscar_por_nombre(datos.nombre)
            if otra is not None and otra.id != zona.id:
                raise ReglaDeNegocioViolada("Ya existe una zona con ese nombre")
            zona.nombre = datos.nombre.strip()
        if datos.codigo is not None:
            zona.codigo = datos.codigo.strip().upper()
        await self._dao.guardar(zona)
        await self._sesion.commit()
        return ZonaResponse.model_validate(zona)

    async def desactivar(self, zona_id: str) -> ZonaResponse:
        zona = await self._buscar_o_fallar(zona_id)
        self._bo.validar_baja(zona.activo)
        zona.activo = False
        await self._dao.guardar(zona)
        await self._sesion.commit()
        return ZonaResponse.model_validate(zona)

    async def _buscar_o_fallar(self, zona_id: str) -> Zona:
        zona = await self._dao.buscar_por_id(zona_id)
        if zona is None:
            raise RecursoNoEncontrado("Zona no encontrada")
        return zona
