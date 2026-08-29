"""DAO del módulo proveedores."""

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.paginacion import calcular_offset
from app.core.tenant_ctx import del_tenant, es_del_tenant
from app.modulos.proveedores.models import ListaProveedorItem, Proveedor


class ProveedorDAO:
    def __init__(self, sesion: AsyncSession) -> None:
        self._sesion = sesion

    async def listar(
        self,
        *,
        q: str | None = None,
        activo: bool | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Proveedor], int]:
        filtros = [del_tenant(Proveedor)]
        if activo is not None:
            filtros.append(Proveedor.activo.is_(activo))
        if q:
            termino = f"%{q.strip()}%"
            filtros.append(
                or_(
                    Proveedor.nombre.ilike(termino),
                    Proveedor.email.ilike(termino),
                    Proveedor.cuit.ilike(termino),
                )
            )

        consulta_total = select(func.count()).select_from(Proveedor).where(*filtros)
        consulta = select(Proveedor).where(*filtros).order_by(Proveedor.nombre)

        total = int((await self._sesion.execute(consulta_total)).scalar_one())
        resultado = await self._sesion.execute(
            consulta.offset(calcular_offset(page, page_size)).limit(page_size)
        )
        return list(resultado.scalars()), total

    async def buscar_por_id(self, proveedor_id: str) -> Proveedor | None:
        proveedor = await self._sesion.get(Proveedor, proveedor_id)
        return proveedor if es_del_tenant(proveedor) else None

    async def guardar(self, proveedor: Proveedor) -> Proveedor:
        self._sesion.add(proveedor)
        await self._sesion.flush()
        return proveedor

    async def buscar_item(self, item_id: str) -> ListaProveedorItem | None:
        item = await self._sesion.get(ListaProveedorItem, item_id)
        return item if es_del_tenant(item) else None

    async def buscar_item_por_codigo(
        self, proveedor_id: str, codigo: str
    ) -> ListaProveedorItem | None:
        codigo_l = codigo.strip()
        if not codigo_l:
            return None
        resultado = await self._sesion.execute(
            select(ListaProveedorItem).where(
                del_tenant(ListaProveedorItem),
                ListaProveedorItem.proveedor_id == proveedor_id,
                ListaProveedorItem.codigo_proveedor == codigo_l,
            )
        )
        return resultado.scalar_one_or_none()

    async def listar_items(
        self,
        proveedor_id: str,
        *,
        q: str | None = None,
        solo_sin_match: bool = False,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[ListaProveedorItem], int]:
        filtros = [
            del_tenant(ListaProveedorItem),
            ListaProveedorItem.proveedor_id == proveedor_id,
        ]
        if solo_sin_match:
            filtros.append(
                or_(
                    ListaProveedorItem.articulo_id == "",
                    ListaProveedorItem.articulo_id.is_(None),
                )
            )
        if q:
            termino = f"%{q.strip()}%"
            filtros.append(
                or_(
                    ListaProveedorItem.codigo_proveedor.ilike(termino),
                    ListaProveedorItem.nombre.ilike(termino),
                )
            )
        total = int(
            (
                await self._sesion.execute(
                    select(func.count()).select_from(ListaProveedorItem).where(*filtros)
                )
            ).scalar_one()
        )
        resultado = await self._sesion.execute(
            select(ListaProveedorItem)
            .where(*filtros)
            .order_by(ListaProveedorItem.nombre, ListaProveedorItem.codigo_proveedor)
            .offset(calcular_offset(page, page_size))
            .limit(page_size)
        )
        return list(resultado.scalars()), total

    async def guardar_item(self, item: ListaProveedorItem) -> ListaProveedorItem:
        self._sesion.add(item)
        await self._sesion.flush()
        return item
