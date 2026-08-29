"""Service compras: pedido → remito (stock) → factura (CxP)."""

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import obtener_configuracion
from app.core.eventos import EventoDominio, bus_eventos
from app.core.excepciones import RecursoNoEncontrado, ReglaDeNegocioViolada
from app.modulos.compras.adaptadores.factory import crear_parser_remito
from app.modulos.compras.bo import ComprasBO
from app.modulos.compras.dao import ComprasDAO
from app.modulos.compras.models import Compra, LineaCompra
from app.modulos.compras.puerto import PuertoParserRemitoVision
from app.modulos.compras.remito_vision import (
    matchear_remito,
    normalizar_media_type,
    validar_imagen_remito,
)
from app.modulos.compras.schemas import (
    CompraResponse,
    CrearCompraRequest,
    LineaRemitoParseadaResponse,
    ParsearRemitoResponse,
)
from app.modulos.cxp.contrato import ContratoCxp, CxpLocal
from app.modulos.parametros.contrato import ContratoParametros, ParametrosLocal
from app.modulos.productos.contrato import ContratoProductos, ProductosLocal
from app.modulos.proveedores.contrato import ContratoProveedores, ProveedoresLocal
from app.modulos.stock.contrato import ContratoStock, StockLocal


class ComprasService:
    def __init__(
        self,
        sesion: AsyncSession,
        proveedores: ContratoProveedores | None = None,
        productos: ContratoProductos | None = None,
        stock: ContratoStock | None = None,
        parametros: ContratoParametros | None = None,
        cxp: ContratoCxp | None = None,
        parser_remito: PuertoParserRemitoVision | None = None,
    ) -> None:
        self._sesion = sesion
        self._dao = ComprasDAO(sesion)
        self._bo = ComprasBO()
        self._proveedores = proveedores or ProveedoresLocal(sesion)
        self._productos = productos or ProductosLocal(sesion)
        self._stock = stock or StockLocal(sesion)
        self._parametros = parametros or ParametrosLocal(sesion)
        self._cxp = cxp or CxpLocal(sesion)
        self._parser_remito = parser_remito

    async def listar(self, tipo: str | None = None) -> list[CompraResponse]:
        compras = await self._dao.listar(tipo=tipo)
        return [await self._a_response(c) for c in compras]

    async def obtener(self, compra_id: str) -> CompraResponse:
        return await self._a_response(await self._buscar_o_fallar(compra_id))

    async def crear(self, datos: CrearCompraRequest) -> CompraResponse:
        self._bo.validar_tipo(datos.tipo)
        self._bo.validar_creacion(len(datos.lineas))
        if not await self._proveedores.existe_proveedor(datos.proveedor_id):
            raise ReglaDeNegocioViolada("Proveedor inexistente o inactivo")
        if datos.tipo != "pedido_compra" and not datos.deposito_id:
            raise ReglaDeNegocioViolada("La compra requiere deposito_id")
        if datos.origen_id:
            origen = await self._dao.buscar_por_id(datos.origen_id)
            if origen is None:
                raise RecursoNoEncontrado("Comprobante de origen no encontrado")
            if datos.tipo == "remito_compra" and origen.tipo != "pedido_compra":
                raise ReglaDeNegocioViolada("El remito solo puede originarse en un pedido")
            if datos.tipo == "factura_compra" and origen.tipo != "remito_compra":
                raise ReglaDeNegocioViolada("La factura solo puede originarse en un remito")

        negocio = await self._parametros.obtener_negocio()
        lineas, totales = await self._armar_lineas(datos)
        neto, iva, total = self._bo.calcular_importes(totales, negocio.iva_porcentaje)

        compra = Compra(
            tipo=datos.tipo,
            proveedor_id=datos.proveedor_id,
            deposito_id=datos.deposito_id or None,
            origen_id=datos.origen_id,
            fecha=datos.fecha or date.today(),
            fecha_entrega=datos.fecha_entrega,
            observaciones=datos.observaciones or "",
            neto=neto,
            iva=iva,
            iva_porcentaje=negocio.iva_porcentaje,
            total=total,
            estado="borrador",
            lineas=lineas,
        )
        await self._dao.guardar(compra)
        await self._sesion.commit()
        await self._sesion.refresh(compra, attribute_names=["lineas"])
        return await self._a_response(compra)

    async def parsear_remito_foto(
        self,
        *,
        contenido: bytes,
        nombre_archivo: str | None,
        content_type: str | None,
        proveedor_id: str | None,
        deposito_id: str | None,
    ) -> ParsearRemitoResponse:
        cfg = obtener_configuracion()
        media_type = normalizar_media_type(nombre_archivo, content_type)
        validar_imagen_remito(
            contenido,
            media_type,
            max_bytes=cfg.remito_parse_max_mb * 1024 * 1024,
        )
        if proveedor_id and not await self._proveedores.existe_proveedor(proveedor_id):
            raise ReglaDeNegocioViolada("Proveedor inexistente o inactivo")

        parser = self._parser_remito or crear_parser_remito()
        extraido = await parser.parsear(contenido, media_type)

        activos = await self._productos.listar_activos()
        por_codigo = {}
        por_sku = {}
        for p in activos:
            # codigo_barras no está en ProductoResumen; se resuelve vía DAO en el loop
            por_sku[p.sku.strip().upper()] = p

        # Índice de códigos de barras (requiere consulta por línea extraída + catálogo)
        for linea in extraido.lineas:
            if linea.codigo_barras:
                prod = await self._productos.obtener_por_codigo_barras(linea.codigo_barras)
                if prod:
                    por_codigo[linea.codigo_barras.strip()] = prod

        matcheado = matchear_remito(
            extraido,
            por_codigo_barras=por_codigo,
            por_sku=por_sku,
            candidatos_nombre=activos,
        )

        modo = cfg.remito_parse_modo.lower()
        if modo == "auto":
            modo_parser = "anthropic" if cfg.anthropic_api_key else "mock"
        else:
            modo_parser = modo

        return ParsearRemitoResponse(
            numero_remito=matcheado.numero_remito,
            fecha=matcheado.fecha,
            proveedor_texto=matcheado.proveedor_texto,
            proveedor_id=proveedor_id,
            deposito_id=deposito_id,
            lineas=[
                LineaRemitoParseadaResponse(
                    descripcion_extraida=linea.descripcion_extraida,
                    sku_extraido=linea.sku_extraido,
                    codigo_barras_extraido=linea.codigo_barras_extraido,
                    cantidad=linea.cantidad,
                    precio_unitario=linea.precio_unitario,
                    producto_id=linea.producto_id,
                    producto_nombre=linea.producto_nombre,
                    producto_sku=linea.producto_sku,
                    match_tipo=linea.match_tipo,
                    confianza=linea.confianza,
                )
                for linea in matcheado.lineas
            ],
            sin_match=matcheado.sin_match,
            advertencias=matcheado.advertencias,
            confianza_extraccion=matcheado.confianza_extraccion,
            modo_parser=modo_parser,
        )

    async def emitir(self, compra_id: str) -> CompraResponse:
        compra = await self._buscar_o_fallar(compra_id)
        self._bo.validar_emitir_pedido(compra.tipo, compra.estado)
        compra.estado = "emitido"
        await self._sesion.commit()
        await self._sesion.refresh(compra, attribute_names=["lineas"])
        await bus_eventos.publicar(
            EventoDominio(
                nombre="compras.pedido.emitido",
                datos={
                    "compra_id": compra.id,
                    "proveedor_id": compra.proveedor_id,
                    "total": compra.total,
                },
            )
        )
        return await self._a_response(compra)

    async def confirmar(self, compra_id: str) -> CompraResponse:
        compra = await self._buscar_o_fallar(compra_id)
        self._bo.validar_confirmacion(compra.tipo, compra.estado, compra.deposito_id)
        assert compra.deposito_id is not None

        if compra.tipo == "remito_compra":
            sin_articulo = sum(1 for linea in compra.lineas if not linea.producto_id)
            self._bo.validar_lineas_con_articulo(sin_articulo)
            for linea in compra.lineas:
                await self._stock.ingresar(
                    articulo_id=linea.producto_id,
                    deposito_id=compra.deposito_id,
                    cantidad=linea.cantidad,
                    referencia=f"{compra.tipo}:{compra.id}",
                )
            compra.estado = "confirmado"
            await self._actualizar_estado_pedido(compra.origen_id)
        else:
            # factura_compra: stock solo si no viene de un remito ya confirmado
            if not compra.origen_id:
                sin_articulo = sum(1 for linea in compra.lineas if not linea.producto_id)
                self._bo.validar_lineas_con_articulo(sin_articulo)
                for linea in compra.lineas:
                    await self._stock.ingresar(
                        articulo_id=linea.producto_id,
                        deposito_id=compra.deposito_id,
                        cantidad=linea.cantidad,
                        referencia=f"{compra.tipo}:{compra.id}",
                    )
            compra.estado = "confirmado"
            await self._imputar_factura_en_cxp(compra)

        await self._sesion.commit()
        await self._sesion.refresh(compra, attribute_names=["lineas"])
        await bus_eventos.publicar(
            EventoDominio(
                nombre=f"compras.{compra.tipo}.confirmado",
                datos={
                    "compra_id": compra.id,
                    "proveedor_id": compra.proveedor_id,
                    "deposito_id": compra.deposito_id,
                    "total": compra.total,
                },
            )
        )
        return await self._a_response(compra)

    async def facturar_remito(self, remito_id: str) -> CompraResponse:
        remito = await self._buscar_o_fallar(remito_id)
        self._bo.validar_conversion_a_factura(remito.tipo, remito.estado)

        lineas = [
            LineaCompra(
                producto_id=linea.producto_id,
                codigo_proveedor=linea.codigo_proveedor or "",
                descripcion=linea.descripcion,
                cantidad=linea.cantidad,
                precio_unitario=linea.precio_unitario,
            )
            for linea in remito.lineas
        ]
        factura = Compra(
            tipo="factura_compra",
            proveedor_id=remito.proveedor_id,
            deposito_id=remito.deposito_id,
            origen_id=remito.id,
            fecha=date.today(),
            neto=remito.neto,
            iva=remito.iva,
            iva_porcentaje=remito.iva_porcentaje,
            total=remito.total,
            estado="confirmado",
            lineas=lineas,
        )
        remito.estado = "facturado"
        await self._dao.guardar(factura)
        await self._imputar_factura_en_cxp(factura)
        await self._sesion.commit()
        await self._sesion.refresh(factura, attribute_names=["lineas"])
        await bus_eventos.publicar(
            EventoDominio(
                nombre="compras.factura_compra.creada",
                datos={
                    "compra_id": factura.id,
                    "origen_id": remito.id,
                    "proveedor_id": factura.proveedor_id,
                    "total": factura.total,
                },
            )
        )
        return await self._a_response(factura)

    async def _imputar_factura_en_cxp(self, factura: Compra) -> None:
        await self._cxp.registrar_debe(
            proveedor_id=factura.proveedor_id,
            monto=factura.total,
            referencia_tipo="factura_compra",
            referencia_id=factura.id,
            concepto=f"Factura compra {factura.numero or factura.id[:8]}",
            fecha=factura.fecha,
        )

    async def _armar_lineas(
        self, datos: CrearCompraRequest
    ) -> tuple[list[LineaCompra], float]:
        lineas: list[LineaCompra] = []
        total = 0.0
        for item in datos.lineas:
            self._bo.validar_linea(item.producto_id, item.codigo_proveedor)
            producto_id = (item.producto_id or "").strip()
            codigo = (item.codigo_proveedor or "").strip()
            descripcion = ""
            costo_lista: float | None = None

            if producto_id:
                producto = await self._productos.obtener_producto(producto_id)
                if producto is None or not producto.activo:
                    raise ReglaDeNegocioViolada(
                        f"Producto inexistente o inactivo: {producto_id}"
                    )
                descripcion = producto.nombre
                costo_lista = producto.costo
                if not codigo:
                    codigo = producto.codigo_proveedor or ""
            elif codigo:
                fila = await self._proveedores.obtener_item(datos.proveedor_id, codigo)
                if fila is None:
                    raise ReglaDeNegocioViolada(
                        f"Código de proveedor no está en la lista: {codigo}"
                    )
                descripcion = fila.nombre
                costo_lista = fila.costo
                producto_id = fila.articulo_id or ""

            precio = (
                item.precio_unitario
                if item.precio_unitario is not None
                else (costo_lista or 0.0)
            )
            lineas.append(
                LineaCompra(
                    producto_id=producto_id,
                    codigo_proveedor=codigo[:40],
                    descripcion=descripcion[:120],
                    cantidad=item.cantidad,
                    precio_unitario=precio,
                )
            )
            total += item.cantidad * precio
        return lineas, total

    async def _actualizar_estado_pedido(self, pedido_id: str | None) -> None:
        if not pedido_id:
            return
        pedido = await self._dao.buscar_por_id(pedido_id)
        if pedido is None or pedido.tipo != "pedido_compra":
            return
        if pedido.estado in {"cerrado", "cancelado", "borrador"}:
            return
        pedida, recibida = await self._cantidades_pedido(pedido)
        pedido.estado = self._bo.estado_pedido_segun_recepcion(pedida, recibida)

    async def _cantidades_pedido(self, pedido: Compra) -> tuple[int, int]:
        pedida = sum(linea.cantidad for linea in pedido.lineas)
        recibida = 0
        for remito in await self._dao.listar_por_origen(pedido.id):
            if remito.tipo != "remito_compra":
                continue
            if remito.estado not in {"confirmado", "facturado"}:
                continue
            recibida += sum(linea.cantidad for linea in remito.lineas)
        return pedida, recibida

    async def _a_response(self, compra: Compra) -> CompraResponse:
        resp = CompraResponse.model_validate(compra)
        if compra.tipo == "pedido_compra":
            pedida, recibida = await self._cantidades_pedido(compra)
            resp.cantidad_pedida = pedida
            resp.cantidad_recibida = recibida
        return resp

    async def _buscar_o_fallar(self, compra_id: str) -> Compra:
        compra = await self._dao.buscar_por_id(compra_id)
        if compra is None:
            raise RecursoNoEncontrado("Compra no encontrada")
        return compra
