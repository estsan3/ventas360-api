"""Casos de uso del módulo IA."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import obtener_configuracion
from app.core.excepciones import ReglaDeNegocioViolada
from app.modulos.clientes.contrato import ClientesLocal, ContratoClientes
from app.modulos.compras.dao import ComprasDAO
from app.modulos.ia.adaptadores.texto import PROMPT_MOSTRADOR, PROMPT_RESUMEN, llamar_haiku_texto
from app.modulos.ia.bo import construir_acciones, narrativa_mock
from app.modulos.ia.mostrador import (
    matchear_lineas_mostrador,
    mostrador_desde_texto_mock,
    parsear_respuesta_llm_mostrador,
)
from app.modulos.ia.schemas import (
    AccionDiaResponse,
    AccionesDiaResponse,
    InterpretarMostradorRequest,
    InterpretarMostradorResponse,
    LineaMostradorInterpretadaResponse,
    ResumenDiaMetricasResponse,
    ResumenDiaResponse,
)
from app.modulos.productos.contrato import ContratoProductos, ProductosLocal
from app.modulos.reporteria.service import ReporteriaService


class IaService:
    def __init__(
        self,
        sesion: AsyncSession,
        clientes: ContratoClientes | None = None,
        productos: ContratoProductos | None = None,
    ) -> None:
        self._sesion = sesion
        self._clientes = clientes or ClientesLocal(sesion)
        self._productos = productos or ProductosLocal(sesion)
        self._reporteria = ReporteriaService(sesion)
        self._compras = ComprasDAO(sesion)

    async def interpretar_mostrador(
        self, datos: InterpretarMostradorRequest
    ) -> InterpretarMostradorResponse:
        cfg = obtener_configuracion()
        if not cfg.ai_habilitada:
            raise ReglaDeNegocioViolada("La IA está deshabilitada en este comercio")

        texto = datos.texto.strip()
        if cfg.anthropic_api_key and cfg.remito_parse_modo != "mock":
            respuesta = llamar_haiku_texto(
                PROMPT_MOSTRADOR,
                f"Pedido del mostrador:\n{texto}",
            )
            extraido = parsear_respuesta_llm_mostrador(respuesta)
            modo = "anthropic"
        else:
            extraido = mostrador_desde_texto_mock(texto)
            modo = "mock"

        activos = await self._productos.listar_activos()
        por_sku = {p.sku.strip().upper(): p for p in activos}

        cliente_id = None
        cliente_nombre = None
        preguntas: list[str] = []
        if extraido.cliente_texto:
            candidatos_cli = await self._clientes.buscar_por_texto(
                extraido.cliente_texto, limite=5
            )
            if len(candidatos_cli) == 1:
                cliente_id = candidatos_cli[0].id
                cliente_nombre = candidatos_cli[0].nombre
            elif candidatos_cli:
                cliente_id = candidatos_cli[0].id
                cliente_nombre = candidatos_cli[0].nombre
                if len(candidatos_cli) > 1:
                    preguntas.append(
                        "Cliente ambiguo: "
                        + ", ".join(c.nombre for c in candidatos_cli[:3])
                    )
            else:
                preguntas.append(
                    f"No encontré cliente '{extraido.cliente_texto}' en el padrón"
                )

        lineas_matcheadas = matchear_lineas_mostrador(
            extraido, por_sku=por_sku, candidatos=activos
        )
        lineas_resp: list[LineaMostradorInterpretadaResponse] = []
        advertencias = list(extraido.advertencias)
        for linea, producto, match_tipo in lineas_matcheadas:
            if producto is None:
                advertencias.append(f"Sin match: {linea.descripcion}")
            lineas_resp.append(
                LineaMostradorInterpretadaResponse(
                    producto_id=producto.id if producto else None,
                    descripcion=linea.descripcion,
                    cantidad=linea.cantidad,
                    precio_unitario=producto.precio if producto else None,
                    producto_nombre=producto.nombre if producto else None,
                    producto_sku=producto.sku if producto else None,
                    match_tipo=match_tipo,
                )
            )

        return InterpretarMostradorResponse(
            tipo=extraido.tipo,
            cliente_id=cliente_id,
            cliente_nombre=cliente_nombre,
            deposito_id=datos.deposito_id,
            lineas=lineas_resp,
            confianza=extraido.confianza,
            advertencias=advertencias,
            preguntas=preguntas,
            modo_parser=modo,
        )

    async def acciones_del_dia(self) -> AccionesDiaResponse:
        kpis = await self._reporteria.obtener_kpis()
        remitos_compra = [
            c for c in await self._compras.listar(tipo="remito_compra") if c.estado == "borrador"
        ]
        acciones = construir_acciones(kpis, remitos_compra_borrador=len(remitos_compra))
        return AccionesDiaResponse(
            acciones=[
                AccionDiaResponse(
                    id=a.id,
                    tipo=a.tipo,
                    prioridad=a.prioridad,
                    titulo=a.titulo,
                    detalle=a.detalle,
                    cantidad=a.cantidad,
                    monto=a.monto,
                    ruta_web=a.ruta_web,
                )
                for a in acciones
            ],
            generado_en=datetime.now(UTC).isoformat(),
        )

    async def resumen_dia(self, *, narrativa: bool = True) -> ResumenDiaResponse:
        kpis = await self._reporteria.obtener_kpis()
        metricas = ResumenDiaMetricasResponse(
            ventas_dia=kpis.ventas_dia,
            monto_ventas_dia=kpis.monto_ventas_dia,
            pedidos_pendientes=kpis.pedidos_pendientes,
            remitos_por_facturar=kpis.remitos_por_facturar,
            saldo_cobrar=kpis.saldo_cobrar,
            saldo_vencido=kpis.saldo_vencido,
            articulos_bajo_stock=kpis.articulos_bajo_stock,
            articulos_sin_stock=kpis.articulos_sin_stock,
            moneda=kpis.moneda,
        )
        acciones = construir_acciones(
            kpis,
            remitos_compra_borrador=len(
                [
                    c
                    for c in await self._compras.listar(tipo="remito_compra")
                    if c.estado == "borrador"
                ]
            ),
        )
        destacadas = [a.titulo for a in acciones[:3]]

        texto_narrativa: str | None = None
        modo_narrativa: str | None = None
        if narrativa:
            cfg = obtener_configuracion()
            payload = metricas.model_dump()
            if cfg.anthropic_api_key and cfg.remito_parse_modo != "mock":
                texto_narrativa = llamar_haiku_texto(
                    PROMPT_RESUMEN,
                    str({"metricas": payload, "acciones": destacadas}),
                )
                modo_narrativa = "anthropic"
            else:
                texto_narrativa = narrativa_mock(kpis)
                modo_narrativa = "mock"

        return ResumenDiaResponse(
            metricas=metricas,
            narrativa=texto_narrativa,
            modo_narrativa=modo_narrativa,
            acciones_destacadas=destacadas,
        )
