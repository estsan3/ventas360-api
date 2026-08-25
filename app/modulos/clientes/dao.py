"""Capa DAO del módulo clientes."""

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.paginacion import calcular_offset
from app.core.tenant_ctx import del_tenant, es_del_tenant
from app.modulos.clientes.models import Cliente


class ClienteDAO:
    """Persistencia de clientes."""

    def __init__(self, sesion: AsyncSession) -> None:
        self._sesion = sesion

    async def listar(
        self,
        *,
        q: str | None = None,
        activo: bool | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Cliente], int]:
        filtros = [del_tenant(Cliente)]
        if activo is not None:
            filtros.append(Cliente.activo.is_(activo))
        if q:
            termino = f"%{q.strip()}%"
            filtros.append(
                or_(
                    Cliente.nombre.ilike(termino),
                    Cliente.email.ilike(termino),
                    Cliente.telefono.ilike(termino),
                    Cliente.cuit.ilike(termino),
                )
            )

        consulta_total = select(func.count()).select_from(Cliente).where(*filtros)
        consulta = select(Cliente).where(*filtros).order_by(Cliente.nombre)

        total = int((await self._sesion.execute(consulta_total)).scalar_one())
        resultado = await self._sesion.execute(
            consulta.offset(calcular_offset(page, page_size)).limit(page_size)
        )
        return list(resultado.scalars()), total

    async def buscar_por_id(self, cliente_id: str) -> Cliente | None:
        cliente = await self._sesion.get(Cliente, cliente_id)
        return cliente if es_del_tenant(cliente) else None

    async def buscar_por_email(self, email: str) -> Cliente | None:
        resultado = await self._sesion.execute(
            select(Cliente).where(del_tenant(Cliente), Cliente.email == email)
        )
        return resultado.scalar_one_or_none()

    async def guardar(self, cliente: Cliente) -> Cliente:
        self._sesion.add(cliente)
        await self._sesion.flush()
        return cliente

    async def contar_activos(self) -> int:
        resultado = await self._sesion.execute(
            select(func.count())
            .select_from(Cliente)
            .where(del_tenant(Cliente), Cliente.activo.is_(True))
        )
        return int(resultado.scalar_one())
