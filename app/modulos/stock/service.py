"""SERVICE del módulo stock."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.excepciones import RecursoNoEncontrado, ReglaDeNegocioViolada
from app.modulos.productos.contrato import ContratoProductos, ProductosLocal
from app.modulos.stock.bo import StockBO
from app.modulos.stock.contrato import StockLocal
from app.modulos.stock.dao import StockDAO
from app.modulos.stock.models import Deposito, MovimientoStock, SaldoStock
from app.modulos.stock.schemas import (
    ActualizarDepositoRequest,
    AjusteStockRequest,
    CrearDepositoRequest,
    DepositoResponse,
    InventarioItemResponse,
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
        self._stock = StockLocal(sesion)

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

    async def actualizar_deposito(
        self, deposito_id: str, datos: ActualizarDepositoRequest
    ) -> DepositoResponse:
        deposito = await self._dao.buscar_deposito(deposito_id)
        if deposito is None:
            raise RecursoNoEncontrado("Depósito no encontrado")
        if datos.nombre is not None:
            deposito.nombre = datos.nombre.strip()
        await self._dao.guardar_deposito(deposito)
        await self._sesion.commit()
        return DepositoResponse.model_validate(deposito)

    async def desactivar_deposito(self, deposito_id: str) -> DepositoResponse:
        deposito = await self._dao.buscar_deposito(deposito_id)
        if deposito is None:
            raise RecursoNoEncontrado("Depósito no encontrado")
        if not deposito.activo:
            raise ReglaDeNegocioViolada("El depósito ya está inactivo")
        deposito.activo = False
        await self._dao.guardar_deposito(deposito)
        await self._sesion.commit()
        return DepositoResponse.model_validate(deposito)

    async def listar_saldos_articulo(self, articulo_id: str) -> list[SaldoResponse]:
        if await self._productos.obtener_producto(articulo_id) is None:
            raise RecursoNoEncontrado("Artículo no encontrado")
        items = await self._dao.listar_saldos_articulo(articulo_id)
        return [SaldoResponse.model_validate(s) for s in items]

    async def listar_inventario_deposito(
        self, deposito_id: str
    ) -> list[InventarioItemResponse]:
        """Catálogo activo + saldo real del depósito.

        Si un artículo tiene stock plano legacy y aún no tiene saldos en ningún
        depósito, lo migra una vez al depósito consultado.
        """
        deposito = await self._dao.buscar_deposito(deposito_id)
        if deposito is None:
            raise RecursoNoEncontrado("Depósito no encontrado")

        articulos = await self._productos.listar_activos()
        saldos = {
            s.articulo_id: s.cantidad
            for s in await self._dao.listar_saldos_deposito(deposito_id)
        }
        migrado = False
        items: list[InventarioItemResponse] = []
        for art in articulos:
            cantidad = saldos.get(art.id)
            if cantidad is None:
                # Migración suave: stock plano del catálogo → saldo de depósito
                if art.stock > 0:
                    saldos_otros = await self._dao.listar_saldos_articulo(art.id)
                    if not saldos_otros:
                        await self._stock.establecer_cantidad(
                            art.id,
                            deposito_id,
                            art.stock,
                            referencia="migracion_stock_plano",
                        )
                        cantidad = art.stock
                        migrado = True
                    else:
                        cantidad = 0
                else:
                    cantidad = 0
            items.append(
                InventarioItemResponse(
                    articulo_id=art.id,
                    sku=art.sku,
                    nombre=art.nombre,
                    deposito_id=deposito_id,
                    cantidad=cantidad,
                    costo=art.costo,
                    precio=art.precio,
                )
            )
        if migrado:
            await self._sesion.commit()
        items.sort(key=lambda i: i.nombre.lower())
        return items

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
