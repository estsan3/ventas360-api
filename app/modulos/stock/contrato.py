"""Contrato público del módulo stock."""

from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.excepciones import RecursoNoEncontrado, ReglaDeNegocioViolada
from app.modulos.stock.bo import StockBO
from app.modulos.stock.dao import StockDAO
from app.modulos.stock.models import MovimientoStock, SaldoStock


class ContratoStock(Protocol):
    async def obtener_saldo(self, articulo_id: str, deposito_id: str) -> int: ...

    async def saldo_total_articulo(self, articulo_id: str) -> int: ...

    async def deposito_default_id(self) -> str | None: ...

    async def establecer_cantidad(
        self,
        articulo_id: str,
        deposito_id: str,
        cantidad: int,
        referencia: str,
    ) -> int: ...

    async def egresar(
        self,
        articulo_id: str,
        deposito_id: str,
        cantidad: int,
        referencia: str,
    ) -> int: ...

    async def ingresar(
        self,
        articulo_id: str,
        deposito_id: str,
        cantidad: int,
        referencia: str,
    ) -> int: ...


class StockLocal:
    """Implementación local: misma sesión/transacción que el service llamador.

    No hace commit: el service orquestador (ej. ventas/compras) controla la TX.
    """

    def __init__(self, sesion: AsyncSession) -> None:
        self._dao = StockDAO(sesion)
        self._bo = StockBO()

    async def obtener_saldo(self, articulo_id: str, deposito_id: str) -> int:
        saldo = await self._dao.buscar_saldo(articulo_id, deposito_id)
        return saldo.cantidad if saldo else 0

    async def saldo_total_articulo(self, articulo_id: str) -> int:
        saldos = await self._dao.listar_saldos_articulo(articulo_id)
        return sum(s.cantidad for s in saldos)

    async def deposito_default_id(self) -> str | None:
        depositos = await self._dao.listar_depositos(solo_activos=True)
        return depositos[0].id if depositos else None

    async def establecer_cantidad(
        self,
        articulo_id: str,
        deposito_id: str,
        cantidad: int,
        referencia: str,
    ) -> int:
        """Ajusta el saldo a una cantidad absoluta (sin commit)."""
        if cantidad < 0:
            raise ReglaDeNegocioViolada("La cantidad de stock no puede ser negativa")
        deposito = await self._dao.buscar_deposito(deposito_id)
        if deposito is None or not deposito.activo:
            raise RecursoNoEncontrado("Depósito no encontrado")
        saldo = await self._dao.buscar_saldo(articulo_id, deposito_id)
        actual = saldo.cantidad if saldo else 0
        delta = cantidad - actual
        if delta == 0:
            return actual
        if saldo is None:
            saldo = SaldoStock(
                articulo_id=articulo_id,
                deposito_id=deposito_id,
                cantidad=0,
            )
        saldo.cantidad = cantidad
        await self._dao.guardar_movimiento(
            MovimientoStock(
                articulo_id=articulo_id,
                deposito_id=deposito_id,
                tipo="ajuste",
                cantidad=delta,
                referencia=referencia,
            )
        )
        await self._dao.guardar_saldo(saldo)
        return saldo.cantidad

    async def egresar(
        self,
        articulo_id: str,
        deposito_id: str,
        cantidad: int,
        referencia: str,
    ) -> int:
        deposito = await self._dao.buscar_deposito(deposito_id)
        if deposito is None or not deposito.activo:
            raise RecursoNoEncontrado("Depósito no encontrado")

        saldo = await self._dao.buscar_saldo(articulo_id, deposito_id)
        actual = saldo.cantidad if saldo else 0
        self._bo.validar_egreso(cantidad, actual)

        if saldo is None:
            raise ReglaDeNegocioViolada("No hay saldo cargado para ese artículo/depósito")

        saldo.cantidad = actual - cantidad
        await self._dao.guardar_movimiento(
            MovimientoStock(
                articulo_id=articulo_id,
                deposito_id=deposito_id,
                tipo="egreso_remito",
                cantidad=-cantidad,
                referencia=referencia,
            )
        )
        await self._dao.guardar_saldo(saldo)
        return saldo.cantidad

    async def ingresar(
        self,
        articulo_id: str,
        deposito_id: str,
        cantidad: int,
        referencia: str,
    ) -> int:
        deposito = await self._dao.buscar_deposito(deposito_id)
        if deposito is None or not deposito.activo:
            raise RecursoNoEncontrado("Depósito no encontrado")

        self._bo.validar_ingreso(cantidad)
        saldo = await self._dao.buscar_saldo(articulo_id, deposito_id)
        if saldo is None:
            saldo = SaldoStock(
                articulo_id=articulo_id,
                deposito_id=deposito_id,
                cantidad=0,
            )
        saldo.cantidad = saldo.cantidad + cantidad
        await self._dao.guardar_movimiento(
            MovimientoStock(
                articulo_id=articulo_id,
                deposito_id=deposito_id,
                tipo="ingreso",
                cantidad=cantidad,
                referencia=referencia,
            )
        )
        await self._dao.guardar_saldo(saldo)
        return saldo.cantidad
