"""SERVICE del módulo precios."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.excepciones import RecursoNoEncontrado, ReglaDeNegocioViolada
from app.modulos.precios.bo import PreciosBO
from app.modulos.precios.contrato import PreciosLocal
from app.modulos.precios.dao import PreciosDAO
from app.modulos.precios.models import ListaPrecio, PrecioArticulo
from app.modulos.precios.schemas import (
    ActualizarListaPrecioRequest,
    CrearListaPrecioRequest,
    ListaPrecioResponse,
    PrecioArticuloResponse,
    PrecioResueltoResponse,
    UpsertPrecioArticuloRequest,
)
from app.modulos.productos.contrato import ContratoProductos, ProductosLocal


class PreciosService:
    def __init__(
        self,
        sesion: AsyncSession,
        productos: ContratoProductos | None = None,
    ) -> None:
        self._sesion = sesion
        self._dao = PreciosDAO(sesion)
        self._bo = PreciosBO()
        self._productos = productos or ProductosLocal(sesion)
        self._resolver = PreciosLocal(sesion, self._productos)

    async def listar_listas(self) -> list[ListaPrecioResponse]:
        items = await self._dao.listar_listas()
        return [ListaPrecioResponse.model_validate(i) for i in items]

    async def crear_lista(self, datos: CrearListaPrecioRequest) -> ListaPrecioResponse:
        if await self._dao.buscar_lista_por_codigo(datos.codigo):
            raise ReglaDeNegocioViolada("Ya existe una lista con ese código")
        if datos.es_default:
            await self._quitar_default_actual()
        lista = ListaPrecio(
            codigo=datos.codigo,
            nombre=datos.nombre,
            es_default=datos.es_default,
        )
        await self._dao.guardar_lista(lista)
        await self._sesion.commit()
        return ListaPrecioResponse.model_validate(lista)

    async def actualizar_lista(
        self, lista_id: str, datos: ActualizarListaPrecioRequest
    ) -> ListaPrecioResponse:
        lista = await self._dao.buscar_lista(lista_id)
        if lista is None:
            raise RecursoNoEncontrado("Lista de precios no encontrada")
        if datos.nombre is not None:
            lista.nombre = datos.nombre.strip()
        if datos.es_default is True:
            await self._quitar_default_actual()
            lista.es_default = True
        elif datos.es_default is False:
            lista.es_default = False
        await self._dao.guardar_lista(lista)
        await self._sesion.commit()
        return ListaPrecioResponse.model_validate(lista)

    async def desactivar_lista(self, lista_id: str) -> ListaPrecioResponse:
        lista = await self._dao.buscar_lista(lista_id)
        if lista is None:
            raise RecursoNoEncontrado("Lista de precios no encontrada")
        if not lista.activo:
            raise ReglaDeNegocioViolada("La lista ya está inactiva")
        if lista.es_default:
            raise ReglaDeNegocioViolada("No se puede desactivar la lista default")
        lista.activo = False
        await self._dao.guardar_lista(lista)
        await self._sesion.commit()
        return ListaPrecioResponse.model_validate(lista)

    async def listar_precios_lista(self, lista_id: str) -> list[PrecioArticuloResponse]:
        if await self._dao.buscar_lista(lista_id) is None:
            raise RecursoNoEncontrado("Lista de precios no encontrada")
        items = await self._dao.listar_precios_lista(lista_id)
        return [PrecioArticuloResponse.model_validate(i) for i in items]

    async def upsert_precio(
        self, datos: UpsertPrecioArticuloRequest
    ) -> PrecioArticuloResponse:
        self._bo.validar_precio(datos.precio)
        if await self._dao.buscar_lista(datos.lista_id) is None:
            raise RecursoNoEncontrado("Lista de precios no encontrada")
        if await self._productos.obtener_producto(datos.articulo_id) is None:
            raise RecursoNoEncontrado("Artículo no encontrado")

        existente = await self._dao.buscar_precio(datos.lista_id, datos.articulo_id)
        if existente is None:
            existente = PrecioArticulo(
                lista_id=datos.lista_id,
                articulo_id=datos.articulo_id,
                precio=datos.precio,
            )
        else:
            existente.precio = datos.precio
        await self._dao.guardar_precio(existente)
        await self._sesion.commit()
        return PrecioArticuloResponse.model_validate(existente)

    async def resolver_precio(
        self, articulo_id: str, cliente_id: str | None = None
    ) -> PrecioResueltoResponse:
        producto = await self._productos.obtener_producto(articulo_id)
        if producto is None:
            raise RecursoNoEncontrado("Artículo no encontrado")

        lista = await self._dao.buscar_lista_default()
        if lista is not None:
            override = await self._dao.buscar_precio(lista.id, articulo_id)
            if override is not None:
                return PrecioResueltoResponse(
                    articulo_id=articulo_id,
                    cliente_id=cliente_id,
                    lista_id=lista.id,
                    precio=override.precio,
                    origen="lista",
                )

        precio = await self._resolver.obtener_precio(articulo_id, cliente_id)
        return PrecioResueltoResponse(
            articulo_id=articulo_id,
            cliente_id=cliente_id,
            lista_id=lista.id if lista else None,
            precio=precio,
            origen="catalogo",
        )

    async def _quitar_default_actual(self) -> None:
        actual = await self._dao.buscar_lista_default()
        if actual is not None:
            actual.es_default = False
            await self._dao.guardar_lista(actual)
