"""Capa DAO del módulo ventas."""

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modulos.ventas.models import Pedido


class VentasDAO:
    """Persistencia de comprobantes."""

    def __init__(self, sesion: AsyncSession) -> None:
        self._sesion = sesion

    async def listar(self, tipo: str | None = None) -> list[Pedido]:
        consulta = (
            select(Pedido)
            .options(selectinload(Pedido.lineas))
            .order_by(Pedido.fecha.desc(), Pedido.id.desc())
        )
        if tipo:
            consulta = consulta.where(Pedido.tipo == tipo)
        resultado = await self._sesion.execute(consulta)
        return list(resultado.scalars())

    async def buscar_por_id(self, pedido_id: str) -> Pedido | None:
        resultado = await self._sesion.execute(
            select(Pedido)
            .options(selectinload(Pedido.lineas))
            .where(Pedido.id == pedido_id)
        )
        return resultado.scalar_one_or_none()

    async def guardar(self, pedido: Pedido) -> Pedido:
        self._sesion.add(pedido)
        await self._sesion.flush()
        return pedido

    async def metricas_mes(self, anio: int, mes: int) -> tuple[int, float]:
        """Cantidad y monto de comprobantes relevantes del mes."""
        inicio = date(anio, mes, 1)
        if mes == 12:
            fin = date(anio + 1, 1, 1)
        else:
            fin = date(anio, mes + 1, 1)

        consulta = (
            select(
                func.count(Pedido.id),
                func.coalesce(func.sum(Pedido.total), 0.0),
            )
            .where(Pedido.fecha >= inicio)
            .where(Pedido.fecha < fin)
            .where(
                Pedido.estado.in_(("confirmado", "entregado", "facturado")),
                Pedido.tipo.in_(("pedido", "remito", "factura")),
            )
        )
        resultado = await self._sesion.execute(consulta)
        cantidad, monto = resultado.one()
        return int(cantidad), float(monto)
