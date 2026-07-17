"""Capa SERVICE del módulo ventas."""

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.excepciones import RecursoNoEncontrado, ReglaDeNegocioViolada
from app.modulos.clientes.contrato import ClientesLocal, ContratoClientes
from app.modulos.productos.contrato import ContratoProductos, ProductosLocal
from app.modulos.ventas.bo import VentasBO
from app.modulos.ventas.dao import VentasDAO
from app.modulos.ventas.models import LineaPedido, Pedido
from app.modulos.ventas.schemas import (
    CambiarEstadoPedidoRequest,
    CrearPedidoRequest,
    PedidoResponse,
)


class VentasService:
    """Casos de uso de pedidos."""

    def __init__(
        self,
        sesion: AsyncSession,
        clientes: ContratoClientes | None = None,
        productos: ContratoProductos | None = None,
    ) -> None:
        self._sesion = sesion
        self._dao = VentasDAO(sesion)
        self._bo = VentasBO()
        self._clientes = clientes or ClientesLocal(sesion)
        self._productos = productos or ProductosLocal(sesion)

    async def listar(self) -> list[PedidoResponse]:
        pedidos = await self._dao.listar()
        return [PedidoResponse.model_validate(p) for p in pedidos]

    async def obtener(self, pedido_id: str) -> PedidoResponse:
        pedido = await self._buscar_o_fallar(pedido_id)
        return PedidoResponse.model_validate(pedido)

    async def crear(self, datos: CrearPedidoRequest) -> PedidoResponse:
        self._bo.validar_creacion(len(datos.lineas))

        if not await self._clientes.existe_cliente(datos.cliente_id):
            raise ReglaDeNegocioViolada("Cliente inexistente o inactivo")

        lineas: list[LineaPedido] = []
        totales: list[tuple[int, float]] = []

        for item in datos.lineas:
            self._bo.validar_cantidad(item.cantidad)
            producto = await self._productos.obtener_producto(item.producto_id)
            if producto is None or not producto.activo:
                raise ReglaDeNegocioViolada(
                    f"Producto inexistente o inactivo: {item.producto_id}"
                )
            lineas.append(
                LineaPedido(
                    producto_id=producto.id,
                    cantidad=item.cantidad,
                    precio_unitario=producto.precio,
                )
            )
            totales.append((item.cantidad, producto.precio))

        pedido = Pedido(
            cliente_id=datos.cliente_id,
            fecha=datos.fecha or date.today(),
            total=self._bo.calcular_total(totales),
            lineas=lineas,
        )
        await self._dao.guardar(pedido)
        await self._sesion.commit()
        await self._sesion.refresh(pedido, attribute_names=["lineas"])
        return PedidoResponse.model_validate(pedido)

    async def cambiar_estado(
        self, pedido_id: str, datos: CambiarEstadoPedidoRequest
    ) -> PedidoResponse:
        pedido = await self._buscar_o_fallar(pedido_id)
        self._bo.validar_transicion(pedido, datos.estado)
        pedido.estado = datos.estado
        await self._sesion.commit()
        return PedidoResponse.model_validate(pedido)

    async def _buscar_o_fallar(self, pedido_id: str) -> Pedido:
        pedido = await self._dao.buscar_por_id(pedido_id)
        if pedido is None:
            raise RecursoNoEncontrado("Pedido no encontrado")
        return pedido
