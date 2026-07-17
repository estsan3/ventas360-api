"""Capa DAO del módulo clientes."""

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.paginacion import calcular_offset
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
        filtros = []
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

        consulta_total = select(func.count()).select_from(Cliente)
        consulta = select(Cliente).order_by(Cliente.nombre)
        if filtros:
            consulta_total = consulta_total.where(*filtros)
            consulta = consulta.where(*filtros)

        total = int((await self._sesion.execute(consulta_total)).scalar_one())
        resultado = await self._sesion.execute(
            consulta.offset(calcular_offset(page, page_size)).limit(page_size)
        )
        return list(resultado.scalars()), total

    async def buscar_por_id(self, cliente_id: str) -> Cliente | None:
        return await self._sesion.get(Cliente, cliente_id)

    async def buscar_por_email(self, email: str) -> Cliente | None:
        resultado = await self._sesion.execute(
            select(Cliente).where(Cliente.email == email)
        )
        return resultado.scalar_one_or_none()

    async def guardar(self, cliente: Cliente) -> Cliente:
        self._sesion.add(cliente)
        await self._sesion.flush()
        return cliente

    async def contar_activos(self) -> int:
        resultado = await self._sesion.execute(
            select(func.count()).select_from(Cliente).where(Cliente.activo.is_(True))
        )
        return int(resultado.scalar_one())
