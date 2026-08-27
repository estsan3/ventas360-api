"""Reglas puras del módulo IA."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from app.core.excepciones import ReglaDeNegocioViolada
from app.modulos.reporteria.schemas import KpisResponse

PRIORIDAD_ALTA = "alta"
PRIORIDAD_MEDIA = "media"
PRIORIDAD_BAJA = "baja"


@dataclass(frozen=True)
class AccionConstruida:
    id: str
    tipo: str
    prioridad: str
    titulo: str
    detalle: str
    cantidad: int
    monto: float | None
    ruta_web: str


def parsear_json_texto(texto: str) -> dict:
    limpio = texto.strip()
    if limpio.startswith("```"):
        limpio = re.sub(r"^```(?:json)?\s*", "", limpio)
        limpio = re.sub(r"\s*```$", "", limpio)
    try:
        data = json.loads(limpio)
    except json.JSONDecodeError as exc:
        raise ReglaDeNegocioViolada(
            "No se pudo interpretar la respuesta del modelo"
        ) from exc
    if not isinstance(data, dict):
        raise ReglaDeNegocioViolada("La respuesta del modelo no es JSON válido")
    return data


def construir_acciones(
    kpis: KpisResponse,
    *,
    remitos_compra_borrador: int,
) -> list[AccionConstruida]:
    acciones: list[AccionConstruida] = []

    if kpis.saldo_vencido > 0:
        vencidos = sum(1 for v in kpis.vencimientos if v.vencido)
        acciones.append(
            AccionConstruida(
                id="cobrar-vencido",
                tipo="cobrar_cxc",
                prioridad=PRIORIDAD_ALTA,
                titulo="Cobrar cuentas vencidas",
                detalle=f"${kpis.saldo_vencido:,.0f} en {vencidos or 'varios'} cliente(s)",
                cantidad=vencidos or 1,
                monto=kpis.saldo_vencido,
                ruta_web="/cuenta-corriente",
            )
        )

    if kpis.remitos_por_facturar > 0:
        acciones.append(
            AccionConstruida(
                id="facturar-remitos",
                tipo="facturar_remito",
                prioridad=PRIORIDAD_ALTA,
                titulo="Facturar remitos confirmados",
                detalle="Remitos de venta listos para factura",
                cantidad=kpis.remitos_por_facturar,
                monto=None,
                ruta_web="/remitos",
            )
        )

    if kpis.pedidos_pendientes > 0:
        acciones.append(
            AccionConstruida(
                id="confirmar-pedidos",
                tipo="confirmar_pedido",
                prioridad=PRIORIDAD_MEDIA,
                titulo="Confirmar pedidos pendientes",
                detalle="Pedidos en borrador esperando preparación",
                cantidad=kpis.pedidos_pendientes,
                monto=None,
                ruta_web="/pedidos",
            )
        )

    if remitos_compra_borrador > 0:
        acciones.append(
            AccionConstruida(
                id="confirmar-remitos-compra",
                tipo="confirmar_remito_compra",
                prioridad=PRIORIDAD_MEDIA,
                titulo="Confirmar remitos de compra",
                detalle="Mercadería recibida sin impactar stock",
                cantidad=remitos_compra_borrador,
                monto=None,
                ruta_web="/inventario?tab=recepcion",
            )
        )

    if kpis.articulos_sin_stock > 0:
        acciones.append(
            AccionConstruida(
                id="sin-stock",
                tipo="reponer_stock",
                prioridad=PRIORIDAD_ALTA,
                titulo="Artículos sin stock",
                detalle="Revisá compras o ajustá inventario",
                cantidad=kpis.articulos_sin_stock,
                monto=None,
                ruta_web="/inventario?tab=alertas",
            )
        )
    elif kpis.articulos_bajo_stock > 0:
        acciones.append(
            AccionConstruida(
                id="bajo-stock",
                tipo="reponer_stock",
                prioridad=PRIORIDAD_MEDIA,
                titulo="Stock bajo mínimo",
                detalle="Artículos por debajo del umbral",
                cantidad=kpis.articulos_bajo_stock,
                monto=None,
                ruta_web="/inventario?tab=alertas",
            )
        )

    if kpis.saldo_cobrar > 0 and kpis.saldo_vencido <= 0:
        acciones.append(
            AccionConstruida(
                id="saldo-cobrar",
                tipo="cobrar_cxc",
                prioridad=PRIORIDAD_BAJA,
                titulo="Saldo en cuenta corriente",
                detalle="Hay deuda sin vencimiento crítico",
                cantidad=len(kpis.vencimientos) or 1,
                monto=kpis.saldo_cobrar,
                ruta_web="/cuenta-corriente",
            )
        )

    if kpis.ventas_dia == 0:
        acciones.append(
            AccionConstruida(
                id="sin-ventas-hoy",
                tipo="vender",
                prioridad=PRIORIDAD_BAJA,
                titulo="Sin ventas hoy",
                detalle="Abrí mostrador o contactá clientes clave",
                cantidad=0,
                monto=0.0,
                ruta_web="/ventas",
            )
        )

    orden = {PRIORIDAD_ALTA: 0, PRIORIDAD_MEDIA: 1, PRIORIDAD_BAJA: 2}
    acciones.sort(key=lambda a: (orden.get(a.prioridad, 9), -a.cantidad))
    return acciones


def narrativa_mock(kpis: KpisResponse) -> str:
    partes = [
        f"Hoy registraste {kpis.ventas_dia} venta(s) por ${kpis.monto_ventas_dia:,.0f}."
    ]
    if kpis.pedidos_pendientes:
        partes.append(f"Hay {kpis.pedidos_pendientes} pedido(s) por confirmar.")
    if kpis.remitos_por_facturar:
        partes.append(f"{kpis.remitos_por_facturar} remito(s) esperan facturación.")
    if kpis.saldo_vencido > 0:
        partes.append(f"Cobranzas vencidas: ${kpis.saldo_vencido:,.0f}.")
    if kpis.articulos_bajo_stock:
        partes.append(
            f"Stock: {kpis.articulos_bajo_stock} artículo(s) bajo mínimo."
        )
    return " ".join(partes)
