"""Adaptadores de texto (Claude Haiku) para IA."""

from __future__ import annotations

from app.core.config import obtener_configuracion
from app.core.excepciones import ReglaDeNegocioViolada

PROMPT_MOSTRADOR = """Interpretá pedidos de mostrador en español rioplatense.
Respondé SOLO JSON válido (sin markdown):
{
  "cliente_texto": "nombre si se menciona o null",
  "tipo": "remito|factura|presupuesto|pedido",
  "confianza": 0.0-1.0,
  "advertencias": [],
  "lineas": [{"descripcion": "...", "cantidad": entero, "sku": null o codigo}]
}
No inventes productos no mencionados."""

PROMPT_RESUMEN = """Sos el asistente de un comercio chico en Argentina.
Con los datos JSON del día, escribí un resumen en 2-4 oraciones, tono directo, español rioplatense.
No uses markdown. No inventes cifras que no estén en los datos."""


def llamar_haiku_texto(prompt_sistema: str, entrada_usuario: str) -> str:
    cfg = obtener_configuracion()
    if not cfg.anthropic_api_key:
        raise ReglaDeNegocioViolada("Falta VENTAS360_ANTHROPIC_API_KEY")
    from anthropic import Anthropic

    client = Anthropic(api_key=cfg.anthropic_api_key)
    try:
        response = client.messages.create(
            model=cfg.anthropic_model,
            max_tokens=min(cfg.anthropic_max_tokens, 1024),
            system=prompt_sistema,
            messages=[{"role": "user", "content": entrada_usuario}],
        )
    except Exception as exc:
        raise ReglaDeNegocioViolada("No se pudo contactar al servicio de IA") from exc
    texto = ""
    for block in response.content:
        if block.type == "text":
            texto += block.text
    if not texto.strip():
        raise ReglaDeNegocioViolada("El modelo no devolvió texto")
    return texto.strip()
