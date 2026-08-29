"""Capa DAO del módulo ventas."""

from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.tenant_ctx import del_tenant, es_del_tenant
from app.modulos.ventas.models import LineaPedido, Pedido


class VentasDAO:
    """Persistencia de comprobantes."""

    def __init__(self, sesion: AsyncSession) -> None:
        self._sesion = sesion

    async def listar_recientes(self, limite: int = 8) -> list[Pedido]:
        resultado = await self._sesion.execute(
            select(Pedido)
            .where(del_tenant(Pedido))
            .where(Pedido.tipo.in_(("pedido", "remito", "factura")))
            .order_by(Pedido.fecha.desc(), Pedido.id.desc())
            .limit(limite)
        )
        return list(resultado.scalars())

    async def serie_diaria(
        self, inicio: date, fin_exclusivo: date
    ) -> dict[date, tuple[int, float]]:
        consulta = (
            select(
                Pedido.fecha,
                func.count(Pedido.id),
                func.coalesce(func.sum(Pedido.total), 0.0),
            )
            .where(del_tenant(Pedido))
            .where(Pedido.fecha >= inicio)
            .where(Pedido.fecha < fin_exclusivo)
            .where(
                Pedido.estado.in_(("confirmado", "entregado", "facturado")),
                Pedido.tipo.in_(("pedido", "remito", "factura")),
            )
            .group_by(Pedido.fecha)
        )
        filas = (await self._sesion.execute(consulta)).all()
        return {fila[0]: (int(fila[1]), float(fila[2])) for fila in filas}

    async def listar(
        self, tipo: str | None = None, cliente_id: str | None = None
    ) -> list[Pedido]:
        consulta = (
            select(Pedido)
            .options(selectinload(Pedido.lineas))
            .where(del_tenant(Pedido))
            .order_by(Pedido.fecha.desc(), Pedido.id.desc())
        )
        if tipo:
            consulta = consulta.where(Pedido.tipo == tipo)
        if cliente_id:
            consulta = consulta.where(Pedido.cliente_id == cliente_id)
        resultado = await self._sesion.execute(consulta)
        return list(resultado.scalars())

    async def max_cbte_nro(self, punto_venta: int, cbte_tipo: int) -> int:
        resultado = await self._sesion.execute(
            select(func.max(Pedido.cbte_nro)).where(
                del_tenant(Pedido),
                Pedido.tipo == "factura",
                Pedido.punto_venta == punto_venta,
                Pedido.cbte_tipo == cbte_tipo,
                Pedido.cae.is_not(None),
            )
        )
        valor = resultado.scalar_one_or_none()
        return int(valor or 0)

    async def buscar_por_id(self, pedido_id: str) -> Pedido | None:
        resultado = await self._sesion.execute(
            select(Pedido)
            .options(selectinload(Pedido.lineas))
            .where(Pedido.id == pedido_id)
        )
        pedido = resultado.scalar_one_or_none()
        return pedido if es_del_tenant(pedido) else None

    async def guardar(self, pedido: Pedido) -> Pedido:
        self._sesion.add(pedido)
        await self._sesion.flush()
        return pedido

    async def metricas_periodo(
        self, inicio: date, fin_exclusivo: date
    ) -> tuple[int, float]:
        """Cantidad y monto de comprobantes relevantes en [inicio, fin)."""
        consulta = (
            select(
                func.count(Pedido.id),
                func.coalesce(func.sum(Pedido.total), 0.0),
            )
            .where(del_tenant(Pedido))
            .where(Pedido.fecha >= inicio)
            .where(Pedido.fecha < fin_exclusivo)
            .where(
                Pedido.estado.in_(("confirmado", "entregado", "facturado")),
                Pedido.tipo.in_(("pedido", "remito", "factura")),
            )
        )
        resultado = await self._sesion.execute(consulta)
        cantidad, monto = resultado.one()
        return int(cantidad), float(monto)

    async def metricas_mes(self, anio: int, mes: int) -> tuple[int, float]:
        inicio = date(anio, mes, 1)
        if mes == 12:
            fin = date(anio + 1, 1, 1)
        else:
            fin = date(anio, mes + 1, 1)
        return await self.metricas_periodo(inicio, fin)

    async def metricas_dia(self, dia: date) -> tuple[int, float]:
        return await self.metricas_periodo(dia, dia + timedelta(days=1))

    async def contar_pendientes(self, tipo: str, estado: str = "borrador") -> int:
        resultado = await self._sesion.execute(
            select(func.count())
            .select_from(Pedido)
            .where(
                del_tenant(Pedido),
                Pedido.tipo == tipo,
                Pedido.estado == estado,
            )
        )
        return int(resultado.scalar_one())

    async def top_articulos(self, limite: int = 5) -> list[tuple[str, str, int, float]]:
        """Top artículos por cantidad vendida (confirmados/facturados)."""
        consulta = (
            select(
                LineaPedido.producto_id,
                func.max(LineaPedido.descripcion),
                func.coalesce(func.sum(LineaPedido.cantidad), 0),
                func.coalesce(
                    func.sum(LineaPedido.cantidad * LineaPedido.precio_unitario), 0.0
                ),
            )
            .join(Pedido, Pedido.id == LineaPedido.pedido_id)
            .where(
                del_tenant(Pedido),
                del_tenant(LineaPedido),
                Pedido.estado.in_(("confirmado", "entregado", "facturado")),
                Pedido.tipo.in_(("pedido", "remito", "factura")),
            )
            .group_by(LineaPedido.producto_id)
            .order_by(func.sum(LineaPedido.cantidad).desc())
            .limit(limite)
        )
        filas = (await self._sesion.execute(consulta)).all()
        return [
            (str(r[0]), str(r[1] or ""), int(r[2]), float(r[3])) for r in filas
        ]
