"""DAO del módulo stock."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modulos.stock.models import Deposito, MovimientoStock, SaldoStock


class StockDAO:
    def __init__(self, sesion: AsyncSession) -> None:
        self._sesion = sesion

    async def listar_depositos(self, solo_activos: bool = True) -> list[Deposito]:
        consulta = select(Deposito).order_by(Deposito.codigo)
        if solo_activos:
            consulta = consulta.where(Deposito.activo.is_(True))
        return list((await self._sesion.execute(consulta)).scalars())

    async def buscar_deposito(self, deposito_id: str) -> Deposito | None:
        return await self._sesion.get(Deposito, deposito_id)

    async def buscar_deposito_por_codigo(self, codigo: str) -> Deposito | None:
        resultado = await self._sesion.execute(
            select(Deposito).where(Deposito.codigo == codigo)
        )
        return resultado.scalar_one_or_none()

    async def guardar_deposito(self, deposito: Deposito) -> Deposito:
        self._sesion.add(deposito)
        await self._sesion.flush()
        return deposito

    async def buscar_saldo(
        self, articulo_id: str, deposito_id: str
    ) -> SaldoStock | None:
        resultado = await self._sesion.execute(
            select(SaldoStock).where(
                SaldoStock.articulo_id == articulo_id,
                SaldoStock.deposito_id == deposito_id,
            )
        )
        return resultado.scalar_one_or_none()

    async def listar_saldos_articulo(self, articulo_id: str) -> list[SaldoStock]:
        resultado = await self._sesion.execute(
            select(SaldoStock).where(SaldoStock.articulo_id == articulo_id)
        )
        return list(resultado.scalars())

    async def guardar_saldo(self, saldo: SaldoStock) -> SaldoStock:
        self._sesion.add(saldo)
        await self._sesion.flush()
        return saldo

    async def guardar_movimiento(self, mov: MovimientoStock) -> MovimientoStock:
        self._sesion.add(mov)
        await self._sesion.flush()
        return mov
