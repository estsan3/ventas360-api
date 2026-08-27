"""Parseo y matching del asistente de mostrador."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.core.excepciones import ReglaDeNegocioViolada
from app.modulos.ia.bo import parsear_json_texto
from app.modulos.productos.contrato import ProductoResumen


@dataclass(frozen=True)
class LineaExtraidaMostrador:
    descripcion: str
    cantidad: int
    sku: str | None = None


@dataclass(frozen=True)
class MostradorExtraido:
    cliente_texto: str | None
    tipo: str
    lineas: list[LineaExtraidaMostrador]
    confianza: float
    advertencias: list[str]


def mostrador_desde_json(data: dict) -> MostradorExtraido:
    lineas_raw = data.get("lineas") or []
    if not isinstance(lineas_raw, list):
        raise ReglaDeNegocioViolada("El campo lineas debe ser una lista")
    lineas: list[LineaExtraidaMostrador] = []
    for item in lineas_raw:
        if not isinstance(item, dict):
            continue
        desc = str(item.get("descripcion") or "").strip()
        if not desc:
            continue
        cantidad = _entero_positivo(item.get("cantidad"), default=1)
        sku = _opcional_str(item.get("sku"))
        lineas.append(LineaExtraidaMostrador(descripcion=desc, cantidad=cantidad, sku=sku))
    if not lineas:
        raise ReglaDeNegocioViolada(
            "No se detectaron productos en el texto. Probá otra frase."
        )
    tipo = str(data.get("tipo") or "remito").strip().lower()
    if tipo not in {"remito", "factura", "presupuesto", "pedido"}:
        tipo = "remito"
    confianza = float(data.get("confianza") or 0.6)
    confianza = max(0.0, min(1.0, confianza))
    advertencias = [str(n) for n in (data.get("advertencias") or []) if str(n).strip()]
    return MostradorExtraido(
        cliente_texto=_opcional_str(data.get("cliente_texto")),
        tipo=tipo,
        lineas=lineas,
        confianza=confianza,
        advertencias=advertencias,
    )


def mostrador_desde_texto_mock(texto: str) -> MostradorExtraido:
    """Parser heurístico para dev local sin API key."""
    t = texto.strip()
    cliente = None
    m_cli = re.search(
        r"(?:para|a|cliente)\s+(.+?)(?:,|$|\.\s|\s+\d|\s+dos|\s+tres|\s+cuatro|\s+cinco|\s+factura|\s+remito)",
        t,
        re.I,
    )
    if m_cli:
        cliente = m_cli.group(1).strip(" .,")

    tipo = "factura" if re.search(r"\bfactura\b", t, re.I) else "remito"
    lineas: list[LineaExtraidaMostrador] = []

    patrones = [
        (r"(\d+)\s+(?:x\s+)?(.+?)(?:\s+y\s+|\s*,|\s*$)", None),
        (r"\b(dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez)\s+(.+?)(?:\s+y\s+|\s*,|\s*$)", {
            "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6,
            "siete": 7, "ocho": 8, "nueve": 9, "diez": 10,
        }),
    ]
    resto = t
    for patron, mapa in patrones:
        for m in re.finditer(patron, resto, re.I):
            if mapa:
                cantidad = mapa[m.group(1).lower()]
                desc = m.group(2).strip(" .,")
            else:
                cantidad = int(m.group(1))
                desc = m.group(2).strip(" .,")
            if desc and len(desc) > 1:
                lineas.append(LineaExtraidaMostrador(descripcion=desc, cantidad=cantidad))

    if not lineas:
        # fallback demo seed
        lineas = [
            LineaExtraidaMostrador(descripcion="Mouse inalámbrico", cantidad=1, sku="MS-010"),
        ]
    return MostradorExtraido(
        cliente_texto=cliente,
        tipo=tipo,
        lineas=lineas,
        confianza=0.65,
        advertencias=["Modo mock: configurá VENTAS360_ANTHROPIC_API_KEY para NLU real."],
    )


def matchear_lineas_mostrador(
    extraido: MostradorExtraido,
    *,
    por_sku: dict[str, ProductoResumen],
    candidatos: list[ProductoResumen],
) -> list[tuple[LineaExtraidaMostrador, ProductoResumen | None, str | None]]:
    resultado: list[tuple[LineaExtraidaMostrador, ProductoResumen | None, str | None]] = []
    for linea in extraido.lineas:
        producto = None
        match_tipo = None
        if linea.sku and linea.sku.upper() in por_sku:
            producto = por_sku[linea.sku.upper()]
            match_tipo = "sku"
        if producto is None:
            desc = linea.descripcion.lower()
            mejor: ProductoResumen | None = None
            mejor_score = 0.0
            for p in candidatos:
                score = _similitud(desc, p.nombre.lower())
                if p.sku.lower() in desc or desc in p.nombre.lower():
                    score = max(score, 0.8)
                if score > mejor_score:
                    mejor_score = score
                    mejor = p
            if mejor is not None and mejor_score >= 0.45:
                producto = mejor
                match_tipo = "nombre"
        resultado.append((linea, producto, match_tipo))
    return resultado


def parsear_respuesta_llm_mostrador(texto: str) -> MostradorExtraido:
    return mostrador_desde_json(parsear_json_texto(texto))


def _similitud(a: str, b: str) -> float:
    if a in b or b in a:
        return 0.85
    ta = set(re.findall(r"[a-z0-9]+", a))
    tb = set(re.findall(r"[a-z0-9]+", b))
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(len(ta), len(tb))


def _opcional_str(valor: object) -> str | None:
    if valor is None:
        return None
    t = str(valor).strip()
    return t or None


def _entero_positivo(valor: object, *, default: int) -> int:
    if valor is None or valor == "":
        return default
    try:
        n = int(float(valor))
    except (TypeError, ValueError):
        return default
    return n if n > 0 else default
