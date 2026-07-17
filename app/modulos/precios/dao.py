"""DAO del módulo precios."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modulos.precios.models import ListaPrecio, PrecioArticulo


class PreciosDAO:
    def __init__(self, sesion: AsyncSession) -> None:
        self._sesion = sesion

    async def listar_listas(self, solo_activas: bool = True) -> list[ListaPrecio]:
        consulta = select(ListaPrecio).order_by(ListaPrecio.codigo)
        if solo_activas:
            consulta = consulta.where(ListaPrecio.activo.is_(True))
        return list((await self._sesion.execute(consulta)).scalars())

    async def buscar_lista(self, lista_id: str) -> ListaPrecio | None:
        return await self._sesion.get(ListaPrecio, lista_id)

    async def buscar_lista_por_codigo(self, codigo: str) -> ListaPrecio | None:
        resultado = await self._sesion.execute(
            select(ListaPrecio).where(ListaPrecio.codigo == codigo)
        )
        return resultado.scalar_one_or_none()

    async def buscar_lista_default(self) -> ListaPrecio | None:
        resultado = await self._sesion.execute(
            select(ListaPrecio).where(
                ListaPrecio.es_default.is_(True),
                ListaPrecio.activo.is_(True),
            )
        )
        return resultado.scalar_one_or_none()

    async def guardar_lista(self, lista: ListaPrecio) -> ListaPrecio:
        self._sesion.add(lista)
        await self._sesion.flush()
        return lista

    async def buscar_precio(
        self, lista_id: str, articulo_id: str
    ) -> PrecioArticulo | None:
        resultado = await self._sesion.execute(
            select(PrecioArticulo).where(
                PrecioArticulo.lista_id == lista_id,
                PrecioArticulo.articulo_id == articulo_id,
            )
        )
        return resultado.scalar_one_or_none()

    async def guardar_precio(self, precio: PrecioArticulo) -> PrecioArticulo:
        self._sesion.add(precio)
        await self._sesion.flush()
        return precio
