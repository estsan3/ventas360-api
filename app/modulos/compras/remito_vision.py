"""Lógica pura: normalizar extracción y matchear productos del catálogo."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Literal

from app.core.excepciones import ReglaDeNegocioViolada
from app.modulos.compras.puerto import LineaRemitoExtraida, RemitoExtraido
from app.modulos.productos.contrato import ProductoResumen

MatchTipo = Literal["codigo_barras", "sku", "nombre", None]
ConfianzaMatch = Literal["alta", "media", "baja"]


@dataclass(frozen=True)
class LineaRemitoMatcheada:
    descripcion_extraida: str
    sku_extraido: str | None
    codigo_barras_extraido: str | None
    cantidad: int
    precio_unitario: float | None
    producto_id: str | None
    producto_nombre: str | None
    producto_sku: str | None
    match_tipo: MatchTipo
    confianza: ConfianzaMatch


@dataclass(frozen=True)
class RemitoMatcheado:
    numero_remito: str | None
    fecha: str | None
    proveedor_texto: str | None
    lineas: list[LineaRemitoMatcheada]
    sin_match: int
    advertencias: list[str]
    confianza_extraccion: float


MIME_PERMITIDOS = frozenset({"image/jpeg", "image/png", "image/webp"})
MAX_BYTES_DEFAULT = 5 * 1024 * 1024


def validar_imagen_remito(
    contenido: bytes,
    media_type: str,
    *,
    max_bytes: int = MAX_BYTES_DEFAULT,
) -> None:
    if not contenido:
        raise ReglaDeNegocioViolada("La imagen está vacía")
    if len(contenido) > max_bytes:
        raise ReglaDeNegocioViolada(
            f"La imagen supera el tamaño máximo ({max_bytes // (1024 * 1024)} MB)"
        )
    if media_type not in MIME_PERMITIDOS:
        raise ReglaDeNegocioViolada(
            "El archivo debe ser una imagen (JPEG, PNG o WebP)"
        )


def normalizar_media_type(nombre: str | None, content_type: str | None) -> str:
    ct = (content_type or "").split(";")[0].strip().lower()
    if ct in MIME_PERMITIDOS:
        return ct
    nombre_l = (nombre or "").lower()
    if nombre_l.endswith(".png"):
        return "image/png"
    if nombre_l.endswith(".webp"):
        return "image/webp"
    if nombre_l.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    raise ReglaDeNegocioViolada(
        "El archivo debe ser una imagen (JPEG, PNG o WebP)"
    )


def parsear_json_modelo(texto: str) -> dict:
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
        raise ReglaDeNegocioViolada("La respuesta del modelo no es un objeto JSON")
    return data


def remito_desde_json(data: dict) -> RemitoExtraido:
    lineas_raw = data.get("lineas") or []
    if not isinstance(lineas_raw, list):
        raise ReglaDeNegocioViolada("El campo lineas debe ser una lista")

    lineas: list[LineaRemitoExtraida] = []
    for item in lineas_raw:
        if not isinstance(item, dict):
            continue
        descripcion = str(item.get("descripcion") or "").strip()
        if not descripcion:
            continue
        cantidad = _entero_positivo(item.get("cantidad"), default=1)
        sku = _opcional_str(item.get("sku") or item.get("codigo"))
        codigo_barras = _opcional_str(item.get("codigo_barras"))
        precio = _opcional_float(item.get("precio_unitario"))
        unidad = _opcional_str(item.get("unidad"))
        lineas.append(
            LineaRemitoExtraida(
                descripcion=descripcion,
                cantidad=cantidad,
                sku=sku,
                codigo_barras=codigo_barras,
                precio_unitario=precio,
                unidad=unidad,
            )
        )

    if not lineas:
        raise ReglaDeNegocioViolada(
            "No se detectaron líneas legibles en el remito. Probá con otra foto."
        )

    confianza = float(data.get("confianza") or 0.5)
    confianza = max(0.0, min(1.0, confianza))
    notas = [str(n) for n in (data.get("notas") or []) if str(n).strip()]

    return RemitoExtraido(
        numero=_opcional_str(data.get("numero")),
        fecha=_opcional_str(data.get("fecha")),
        proveedor_texto=_opcional_str(data.get("proveedor_texto")),
        lineas=lineas,
        confianza=confianza,
        notas=notas,
    )


def matchear_remito(
    extraido: RemitoExtraido,
    *,
    por_codigo_barras: dict[str, ProductoResumen],
    por_sku: dict[str, ProductoResumen],
    candidatos_nombre: list[ProductoResumen],
) -> RemitoMatcheado:
    lineas: list[LineaRemitoMatcheada] = []
    sin_match = 0

    for linea in extraido.lineas:
        producto, match_tipo, confianza = _matchear_linea(
            linea,
            por_codigo_barras=por_codigo_barras,
            por_sku=por_sku,
            candidatos_nombre=candidatos_nombre,
        )
        if producto is None:
            sin_match += 1
        lineas.append(
            LineaRemitoMatcheada(
                descripcion_extraida=linea.descripcion,
                sku_extraido=linea.sku,
                codigo_barras_extraido=linea.codigo_barras,
                cantidad=linea.cantidad,
                precio_unitario=linea.precio_unitario,
                producto_id=producto.id if producto else None,
                producto_nombre=producto.nombre if producto else None,
                producto_sku=producto.sku if producto else None,
                match_tipo=match_tipo,
                confianza=confianza,
            )
        )

    advertencias = list(extraido.notas)
    if sin_match:
        advertencias.append(
            f"{sin_match} línea{'s' if sin_match != 1 else ''} sin artículo en el catálogo"
        )

    return RemitoMatcheado(
        numero_remito=extraido.numero,
        fecha=extraido.fecha,
        proveedor_texto=extraido.proveedor_texto,
        lineas=lineas,
        sin_match=sin_match,
        advertencias=advertencias,
        confianza_extraccion=extraido.confianza,
    )


def _matchear_linea(
    linea: LineaRemitoExtraida,
    *,
    por_codigo_barras: dict[str, ProductoResumen],
    por_sku: dict[str, ProductoResumen],
    candidatos_nombre: list[ProductoResumen],
) -> tuple[ProductoResumen | None, MatchTipo, ConfianzaMatch]:
    if linea.codigo_barras:
        codigo = linea.codigo_barras.strip()
        if codigo in por_codigo_barras:
            return por_codigo_barras[codigo], "codigo_barras", "alta"

    if linea.sku:
        sku = linea.sku.strip().upper()
        if sku in por_sku:
            return por_sku[sku], "sku", "alta"

    desc = linea.descripcion.lower()
    mejor: ProductoResumen | None = None
    mejor_score = 0.0
    for producto in candidatos_nombre:
        score = _similitud_nombre(desc, producto.nombre.lower())
        if score > mejor_score:
            mejor_score = score
            mejor = producto
    if mejor is not None and mejor_score >= 0.55:
        conf: ConfianzaMatch = "media" if mejor_score >= 0.75 else "baja"
        return mejor, "nombre", conf

    return None, None, "baja"


def _similitud_nombre(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    if a in b or b in a:
        return 0.85
    tokens_a = set(re.findall(r"[a-z0-9]+", a))
    tokens_b = set(re.findall(r"[a-z0-9]+", b))
    if not tokens_a or not tokens_b:
        return 0.0
    inter = tokens_a & tokens_b
    return len(inter) / max(len(tokens_a), len(tokens_b))


def _opcional_str(valor: object) -> str | None:
    if valor is None:
        return None
    texto = str(valor).strip()
    return texto or None


def _opcional_float(valor: object) -> float | None:
    if valor is None or valor == "":
        return None
    try:
        n = float(valor)
    except (TypeError, ValueError):
        return None
    return n if n >= 0 else None


def _entero_positivo(valor: object, *, default: int) -> int:
    if valor is None or valor == "":
        return default
    try:
        n = int(float(valor))
    except (TypeError, ValueError):
        return default
    return n if n > 0 else default
