"""Capa SERVICE del módulo ventas: comprobantes tipados."""

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.eventos import EventoDominio, bus_eventos
from app.core.excepciones import RecursoNoEncontrado, ReglaDeNegocioViolada
from app.modulos.clientes.contrato import ClientesLocal, ContratoClientes
from app.modulos.cxc.contrato import ContratoCxc, CxcLocal
from app.modulos.parametros.contrato import ContratoParametros, ParametrosLocal
from app.modulos.precios.contrato import ContratoPrecios, PreciosLocal
from app.modulos.productos.contrato import ContratoProductos, ProductosLocal
from app.modulos.stock.contrato import ContratoStock, StockLocal
from app.modulos.ventas.adaptadores import crear_proveedor_fe
from app.modulos.ventas.bo import VentasBO
from app.modulos.ventas.dao import VentasDAO
from app.modulos.ventas.fiscal import (
    IdentidadFiscal,
    armar_identidad,
    armar_qr,
    formatear_numero_fiscal,
    id_alicuota,
    validar_emision_fiscal,
)
from app.modulos.ventas.models import LineaPedido, Pedido
from app.modulos.ventas.puerto import ProveedorFE, SolicitudFE
from app.modulos.ventas.schemas import (
    CambiarEstadoPedidoRequest,
    CrearPedidoRequest,
    PedidoResponse,
)


class VentasService:
    """Casos de uso de pedidos, remitos y facturas."""

    def __init__(
        self,
        sesion: AsyncSession,
        clientes: ContratoClientes | None = None,
        productos: ContratoProductos | None = None,
        precios: ContratoPrecios | None = None,
        stock: ContratoStock | None = None,
        parametros: ContratoParametros | None = None,
        cxc: ContratoCxc | None = None,
        proveedor_fe: ProveedorFE | None = None,
    ) -> None:
        self._sesion = sesion
        self._dao = VentasDAO(sesion)
        self._bo = VentasBO()
        self._clientes = clientes or ClientesLocal(sesion)
        self._productos = productos or ProductosLocal(sesion)
        self._precios = precios or PreciosLocal(sesion)
        self._stock = stock or StockLocal(sesion)
        self._parametros = parametros or ParametrosLocal(sesion)
        self._cxc = cxc or CxcLocal(sesion)
        self._fe = proveedor_fe or crear_proveedor_fe()

    async def listar(
        self, tipo: str | None = None, cliente_id: str | None = None
    ) -> list[PedidoResponse]:
        pedidos = await self._dao.listar(tipo=tipo, cliente_id=cliente_id)
        return [PedidoResponse.model_validate(p) for p in pedidos]

    async def obtener(self, pedido_id: str) -> PedidoResponse:
        pedido = await self._buscar_o_fallar(pedido_id)
        return PedidoResponse.model_validate(pedido)

    async def crear(self, datos: CrearPedidoRequest) -> PedidoResponse:
        self._bo.validar_tipo(datos.tipo)
        self._bo.validar_creacion(len(datos.lineas))

        if not await self._clientes.existe_cliente(datos.cliente_id):
            raise ReglaDeNegocioViolada("Cliente inexistente o inactivo")

        if datos.tipo == "remito" and not datos.deposito_id:
            raise ReglaDeNegocioViolada("El remito requiere deposito_id")

        negocio = await self._parametros.obtener_negocio()
        lineas, totales = await self._armar_lineas(datos)
        identidad = (
            await self._identidad_de_cliente(datos.cliente_id, negocio.iva_porcentaje)
            if datos.tipo == "factura"
            else None
        )
        iva_pct = identidad.iva_porcentaje if identidad else negocio.iva_porcentaje

        neto, iva, total = self._bo.calcular_importes(totales, iva_pct)
        numero: str | None = None
        try:
            numero = await self._parametros.asignar_numero(datos.tipo)
        except RecursoNoEncontrado:
            numero = None

        pedido = Pedido(
            tipo=datos.tipo,
            cliente_id=datos.cliente_id,
            deposito_id=datos.deposito_id,
            origen_id=datos.origen_id,
            fecha=datos.fecha or date.today(),
            neto=neto,
            iva=iva,
            iva_porcentaje=iva_pct,
            total=total,
            numero=numero,
            lineas=lineas,
        )
        self._aplicar_identidad(pedido, identidad)
        await self._dao.guardar(pedido)
        await self._sesion.commit()
        await self._sesion.refresh(pedido, attribute_names=["lineas"])
        await bus_eventos.publicar(
            EventoDominio(
                nombre=f"ventas.{datos.tipo}.creado",
                datos={
                    "comprobante_id": pedido.id,
                    "cliente_id": pedido.cliente_id,
                    "tipo": pedido.tipo,
                },
            )
        )
        return PedidoResponse.model_validate(pedido)

    async def cambiar_estado(
        self, pedido_id: str, datos: CambiarEstadoPedidoRequest
    ) -> PedidoResponse:
        pedido = await self._buscar_o_fallar(pedido_id)

        # Remito → confirmado usa el flujo con stock.
        if pedido.tipo == "remito" and datos.estado == "confirmado":
            return await self.confirmar_remito(pedido_id)

        self._bo.validar_transicion(pedido.tipo, pedido.estado, datos.estado)
        estado_anterior = pedido.estado
        if pedido.tipo == "factura" and datos.estado == "confirmado":
            await self._autorizar_factura(pedido)
        pedido.estado = datos.estado
        if pedido.tipo == "factura" and datos.estado == "confirmado":
            await self._imputar_factura_en_cxc(pedido)
        await self._sesion.commit()
        await bus_eventos.publicar(
            EventoDominio(
                nombre=f"ventas.{pedido.tipo}.estado_cambiado",
                datos={
                    "comprobante_id": pedido.id,
                    "estado_anterior": estado_anterior,
                    "estado": pedido.estado,
                },
            )
        )
        return PedidoResponse.model_validate(pedido)

    async def confirmar_remito(self, remito_id: str) -> PedidoResponse:
        """Confirma remito y descuenta stock del depósito (misma TX)."""
        remito = await self._buscar_o_fallar(remito_id)
        self._bo.validar_confirmacion_remito(
            remito.tipo, remito.estado, remito.deposito_id
        )
        assert remito.deposito_id is not None

        for linea in remito.lineas:
            await self._stock.egresar(
                articulo_id=linea.producto_id,
                deposito_id=remito.deposito_id,
                cantidad=linea.cantidad,
                referencia=f"remito:{remito.id}",
            )

        remito.estado = "confirmado"
        # El remito entregado ya genera deuda en CxC (luego se factura sin duplicar).
        await self._imputar_comprobante_en_cxc(remito, referencia_tipo="remito")
        await self._sesion.commit()
        await self._sesion.refresh(remito, attribute_names=["lineas"])
        await bus_eventos.publicar(
            EventoDominio(
                nombre="ventas.remito.confirmado",
                datos={
                    "comprobante_id": remito.id,
                    "deposito_id": remito.deposito_id,
                    "cliente_id": remito.cliente_id,
                    "total": remito.total,
                },
            )
        )
        return PedidoResponse.model_validate(remito)

    async def convertir_remito_a_factura(self, remito_id: str) -> PedidoResponse:
        """Genera factura desde remito confirmado y marca el remito facturado.

        La deuda ya se imputó al confirmar el remito. Solo se imputa la factura
        si el remito no tiene movimiento CxC (datos legacy).
        """
        remito = await self._buscar_o_fallar(remito_id)
        self._bo.validar_conversion_a_factura(remito.tipo, remito.estado)

        lineas = [
            LineaPedido(
                producto_id=linea.producto_id,
                descripcion=linea.descripcion,
                cantidad=linea.cantidad,
                precio_unitario=linea.precio_unitario,
            )
            for linea in remito.lineas
        ]
        numero_factura: str | None = None
        try:
            numero_factura = await self._parametros.asignar_numero("factura")
        except RecursoNoEncontrado:
            numero_factura = None

        identidad = await self._identidad_de_cliente(
            remito.cliente_id, remito.iva_porcentaje
        )
        iva_pct = identidad.iva_porcentaje if identidad else remito.iva_porcentaje
        neto, iva, total = remito.neto, remito.iva, remito.total
        if identidad and identidad.iva_porcentaje != remito.iva_porcentaje:
            neto, iva, total = self._bo.calcular_importes(
                [(ln.cantidad, ln.precio_unitario) for ln in remito.lineas],
                iva_pct,
            )

        factura = Pedido(
            tipo="factura",
            cliente_id=remito.cliente_id,
            deposito_id=remito.deposito_id,
            origen_id=remito.id,
            fecha=date.today(),
            neto=neto,
            iva=iva,
            iva_porcentaje=iva_pct,
            total=total,
            numero=numero_factura,
            estado="borrador",
            lineas=lineas,
        )
        self._aplicar_identidad(factura, identidad)
        await self._autorizar_factura(factura)
        factura.estado = "confirmado"
        remito.estado = "facturado"
        await self._dao.guardar(factura)
        remito_ya_en_cxc = await self._cxc.existe_referencia("remito", remito.id)
        if not remito_ya_en_cxc:
            await self._imputar_comprobante_en_cxc(factura, referencia_tipo="factura")
        await self._sesion.commit()
        await self._sesion.refresh(factura, attribute_names=["lineas"])
        await bus_eventos.publicar(
            EventoDominio(
                nombre="ventas.factura.creada",
                datos={
                    "comprobante_id": factura.id,
                    "origen_id": remito.id,
                    "cliente_id": factura.cliente_id,
                    "total": factura.total,
                },
            )
        )
        return PedidoResponse.model_validate(factura)

    async def _imputar_factura_en_cxc(self, factura: Pedido) -> None:
        """Registra el debe de una factura (idempotente por referencia)."""
        await self._imputar_comprobante_en_cxc(factura, referencia_tipo="factura")

    async def _imputar_comprobante_en_cxc(
        self, comprobante: Pedido, *, referencia_tipo: str
    ) -> None:
        """Registra el debe en cuenta corriente (idempotente por referencia)."""
        etiqueta = "Remito" if referencia_tipo == "remito" else "Factura"
        numero = (comprobante.numero or "").strip() or comprobante.id[:8]
        await self._cxc.registrar_debe(
            cliente_id=comprobante.cliente_id,
            monto=comprobante.total,
            referencia_tipo=referencia_tipo,
            referencia_id=comprobante.id,
            concepto=f"{etiqueta} {numero}",
            fecha=comprobante.fecha,
        )

    async def _identidad_de_cliente(
        self, cliente_id: str, iva_porcentaje: float
    ) -> IdentidadFiscal:
        cliente = await self._clientes.obtener_fiscal(cliente_id)
        if cliente is None:
            raise ReglaDeNegocioViolada("Cliente inexistente o inactivo")
        emisor = await self._parametros.obtener_afip()
        return armar_identidad(
            habilitada=emisor.habilitada,
            cuit_emisor=emisor.cuit,
            emisor_iva=emisor.condicion_iva,
            punto_venta=emisor.punto_venta,
            receptor_iva=cliente.condicion_iva,
            cuit_receptor=cliente.cuit,
            iva_porcentaje=iva_porcentaje,
        )

    @staticmethod
    def _aplicar_identidad(pedido: Pedido, identidad: IdentidadFiscal | None) -> None:
        if identidad is None:
            return
        pedido.letra = identidad.letra
        pedido.cbte_tipo = identidad.cbte_tipo
        pedido.punto_venta = identidad.punto_venta
        pedido.doc_tipo = identidad.doc_tipo
        pedido.doc_nro = identidad.doc_nro

    async def _autorizar_factura(self, factura: Pedido) -> None:
        """Pide CAE si ARCA está habilitada. No cambia el estado."""
        if factura.cae:
            return
        emisor = await self._parametros.obtener_afip()
        if not emisor.habilitada:
            return
        identidad = await self._identidad_de_cliente(
            factura.cliente_id, factura.iva_porcentaje
        )
        self._aplicar_identidad(factura, identidad)
        validar_emision_fiscal(
            habilitada=True,
            cuit_emisor=emisor.cuit,
            punto_venta=emisor.punto_venta,
            letra=identidad.letra,
            doc_tipo=identidad.doc_tipo,
            doc_nro=identidad.doc_nro,
        )
        pto = identidad.punto_venta
        tipo = identidad.cbte_tipo
        cuit = identidad.cuit_emisor
        ultimo = await self._fe.ultimo_autorizado(
            cuit_emisor=cuit, punto_venta=pto, cbte_tipo=tipo
        )
        local = await self._dao.max_cbte_nro(pto, tipo)
        nro = max(ultimo, local) + 1
        letra_c = identidad.letra == "C"
        imp_neto = factura.total if letra_c else factura.neto
        imp_iva = 0.0 if letra_c else factura.iva
        solicitud = SolicitudFE(
            cuit_emisor=cuit,
            punto_venta=pto,
            cbte_tipo=tipo,
            cbte_nro=nro,
            concepto=1,
            doc_tipo=identidad.doc_tipo,
            doc_nro=identidad.doc_nro,
            fecha=factura.fecha,
            imp_total=factura.total,
            imp_neto=imp_neto,
            imp_iva=imp_iva,
            imp_tot_conc=0.0,
            iva_id=None if letra_c else id_alicuota(factura.iva_porcentaje),
            condicion_iva_receptor=identidad.condicion_iva_receptor,
        )
        resultado = await self._fe.solicitar_cae(solicitud)
        if not resultado.autorizada or not resultado.cae:
            raise ReglaDeNegocioViolada(
                f"ARCA rechazó la factura: {resultado.error or 'sin CAE'}"
            )
        factura.cae = resultado.cae
        factura.cae_vencimiento = resultado.cae_vencimiento
        factura.cbte_nro = resultado.cbte_nro or nro
        factura.punto_venta = pto
        nro_fiscal = factura.cbte_nro
        factura.numero = formatear_numero_fiscal(identidad.letra, pto, nro_fiscal)
        factura.qr_url = armar_qr(
            fecha=factura.fecha,
            cuit_emisor=cuit,
            punto_venta=pto,
            cbte_tipo=tipo,
            cbte_nro=nro_fiscal,
            importe=factura.total,
            doc_tipo=identidad.doc_tipo,
            doc_nro=identidad.doc_nro,
            cae=resultado.cae,
        )

    async def _armar_lineas(
        self, datos: CrearPedidoRequest
    ) -> tuple[list[LineaPedido], list[tuple[int, float]]]:
        lineas: list[LineaPedido] = []
        totales: list[tuple[int, float]] = []
        for item in datos.lineas:
            self._bo.validar_cantidad(item.cantidad)
            producto = await self._productos.obtener_producto(item.producto_id)
            if producto is None or not producto.activo:
                raise ReglaDeNegocioViolada(
                    f"Producto inexistente o inactivo: {item.producto_id}"
                )
            precio = await self._precios.obtener_precio(
                item.producto_id, datos.cliente_id
            )
            lineas.append(
                LineaPedido(
                    producto_id=producto.id,
                    descripcion=producto.nombre,
                    cantidad=item.cantidad,
                    precio_unitario=precio,
                )
            )
            totales.append((item.cantidad, precio))
        return lineas, totales

    async def _buscar_o_fallar(self, pedido_id: str) -> Pedido:
        pedido = await self._dao.buscar_por_id(pedido_id)
        if pedido is None:
            raise RecursoNoEncontrado("Comprobante no encontrado")
        return pedido
