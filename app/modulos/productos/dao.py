"""Capa DAO del módulo productos."""

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.paginacion import calcular_offset
from app.core.tenant_ctx import del_tenant, es_del_tenant
from app.modulos.productos.models import Producto


class ProductoDAO:
    """Persistencia de productos."""

    def __init__(self, sesion: AsyncSession) -> None:
        self._sesion = sesion

    async def listar(
        self,
        *,
        q: str | None = None,
        activo: bool | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Producto], int]:
        filtros = [del_tenant(Producto)]
        if activo is not None:
            filtros.append(Producto.activo.is_(activo))
        if q:
            termino = f"%{q.strip()}%"
            filtros.append(
                or_(
                    Producto.sku.ilike(termino),
                    Producto.nombre.ilike(termino),
                    Producto.codigo_barras.ilike(termino),
                    Producto.marca.ilike(termino),
                    Producto.rubro.ilike(termino),
                )
            )

        consulta_total = select(func.count()).select_from(Producto).where(*filtros)
        consulta = select(Producto).where(*filtros).order_by(Producto.nombre)

        total = int((await self._sesion.execute(consulta_total)).scalar_one())
        resultado = await self._sesion.execute(
            consulta.offset(calcular_offset(page, page_size)).limit(page_size)
        )
        return list(resultado.scalars()), total

    async def buscar_por_id(self, producto_id: str) -> Producto | None:
        producto = await self._sesion.get(Producto, producto_id)
        return producto if es_del_tenant(producto) else None

    async def buscar_por_sku(self, sku: str) -> Producto | None:
        resultado = await self._sesion.execute(
            select(Producto).where(del_tenant(Producto), Producto.sku == sku)
        )
        return resultado.scalar_one_or_none()

    async def buscar_por_codigo_barras(self, codigo: str) -> Producto | None:
        codigo_l = codigo.strip()
        if not codigo_l:
            return None
        resultado = await self._sesion.execute(
            select(Producto).where(
                del_tenant(Producto),
                Producto.codigo_barras == codigo_l,
                Producto.activo.is_(True),
            )
        )
        return resultado.scalar_one_or_none()

    async def guardar(self, producto: Producto) -> Producto:
        self._sesion.add(producto)
        await self._sesion.flush()
        return producto

    async def listar_activos(self) -> list[Producto]:
        resultado = await self._sesion.execute(
            select(Producto)
            .where(del_tenant(Producto), Producto.activo.is_(True))
            .order_by(Producto.nombre)
        )
        return list(resultado.scalars())

    async def contar_activos(self) -> int:
        resultado = await self._sesion.execute(
            select(func.count())
            .select_from(Producto)
            .where(del_tenant(Producto), Producto.activo.is_(True))
        )
        return int(resultado.scalar_one())

    async def contar_bajo_stock(self, umbral: int = 5) -> tuple[int, int]:
        """(artículos con stock < umbral, artículos en 0). Solo activos."""
        filtros = [del_tenant(Producto), Producto.activo.is_(True)]
        bajo = int(
            (
                await self._sesion.execute(
                    select(func.count())
                    .select_from(Producto)
                    .where(*filtros, Producto.stock < umbral)
                )
            ).scalar_one()
        )
        sin_stock = int(
            (
                await self._sesion.execute(
                    select(func.count())
                    .select_from(Producto)
                    .where(*filtros, Producto.stock <= 0)
                )
            ).scalar_one()
        )
        return bajo, sin_stock

    async def listar_bajo_stock(
        self, *, umbral: int = 5, limite: int = 8
    ) -> list[Producto]:
        resultado = await self._sesion.execute(
            select(Producto)
            .where(
                del_tenant(Producto),
                Producto.activo.is_(True),
                Producto.stock < umbral,
            )
            .order_by(Producto.stock.asc(), Producto.nombre.asc())
            .limit(limite)
        )
        return list(resultado.scalars())

    async def stock_total(self) -> int:
        resultado = await self._sesion.execute(
            select(func.coalesce(func.sum(Producto.stock), 0)).where(
                del_tenant(Producto), Producto.activo.is_(True)
            )
        )
        return int(resultado.scalar_one())
