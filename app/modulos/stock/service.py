"""SERVICE del módulo stock."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.excepciones import RecursoNoEncontrado, ReglaDeNegocioViolada
from app.modulos.productos.contrato import ContratoProductos, ProductosLocal
from app.modulos.stock.bo import StockBO
from app.modulos.stock.dao import StockDAO
from app.modulos.stock.models import Deposito, MovimientoStock, SaldoStock
from app.modulos.stock.schemas import (
    AjusteStockRequest,
    CrearDepositoRequest,
    DepositoResponse,
    SaldoResponse,
)


class StockService:
    def __init__(
        self,
        sesion: AsyncSession,
        productos: ContratoProductos | None = None,
    ) -> None:
        self._sesion = sesion
        self._dao = StockDAO(sesion)
        self._bo = StockBO()
        self._productos = productos or ProductosLocal(sesion)

    async def listar_depositos(self) -> list[DepositoResponse]:
        items = await self._dao.listar_depositos()
        return [DepositoResponse.model_validate(d) for d in items]

    async def crear_deposito(self, datos: CrearDepositoRequest) -> DepositoResponse:
        if await self._dao.buscar_deposito_por_codigo(datos.codigo):
            raise ReglaDeNegocioViolada("Ya existe un depósito con ese código")
        deposito = Deposito(codigo=datos.codigo, nombre=datos.nombre)
        await self._dao.guardar_deposito(deposito)
        await self._sesion.commit()
        return DepositoResponse.model_validate(deposito)

    async def listar_saldos_articulo(self, articulo_id: str) -> list[SaldoResponse]:
        if await self._productos.obtener_producto(articulo_id) is None:
            raise RecursoNoEncontrado("Artículo no encontrado")
        items = await self._dao.listar_saldos_articulo(articulo_id)
        return [SaldoResponse.model_validate(s) for s in items]

    async def ajustar(self, datos: AjusteStockRequest) -> SaldoResponse:
        if await self._productos.obtener_producto(datos.articulo_id) is None:
            raise RecursoNoEncontrado("Artículo no encontrado")
        deposito = await self._dao.buscar_deposito(datos.deposito_id)
        if deposito is None or not deposito.activo:
            raise RecursoNoEncontrado("Depósito no encontrado")

        saldo = await self._dao.buscar_saldo(datos.articulo_id, datos.deposito_id)
        actual = saldo.cantidad if saldo else 0
        self._bo.validar_ajuste(datos.cantidad, actual)

        if saldo is None:
            saldo = SaldoStock(
                articulo_id=datos.articulo_id,
                deposito_id=datos.deposito_id,
                cantidad=0,
            )
        saldo.cantidad = actual + datos.cantidad
        await self._dao.guardar_saldo(saldo)
        await self._dao.guardar_movimiento(
            MovimientoStock(
                articulo_id=datos.articulo_id,
                deposito_id=datos.deposito_id,
                tipo="ajuste",
                cantidad=datos.cantidad,
                referencia=datos.referencia,
            )
        )
        await self._sesion.commit()
        return SaldoResponse.model_validate(saldo)
