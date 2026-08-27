"""Adaptador Anthropic Claude Haiku (visión) para remitos de compra."""

import base64

from anthropic import Anthropic

from app.core.config import obtener_configuracion
from app.core.excepciones import ReglaDeNegocioViolada
from app.modulos.compras.puerto import PuertoParserRemitoVision, RemitoExtraido
from app.modulos.compras.remito_vision import parsear_json_modelo, remito_desde_json

PROMPT = """Sos un asistente que extrae datos de remitos de compra argentinos a partir de fotos.
Respondé ÚNICAMENTE con un objeto JSON válido (sin markdown) con esta forma:
{
  "numero": "string o null",
  "fecha": "YYYY-MM-DD o null",
  "proveedor_texto": "string o null",
  "confianza": 0.0-1.0,
  "notas": ["advertencias sobre ilegibilidad"],
  "lineas": [
    {
      "descripcion": "texto del artículo",
      "cantidad": entero positivo,
      "sku": "código interno si aparece o null",
      "codigo_barras": "EAN/código si aparece o null",
      "precio_unitario": número o null,
      "unidad": "bulto|caja|unidad|etc o null"
    }
  ]
}
Reglas:
- No inventes líneas que no se lean en la imagen.
- Si una cantidad no es legible, omití esa línea o poné nota en "notas".
- cantidad debe ser entero >= 1.
- Si no hay líneas legibles, devolvé lineas: [] y explicá en notas."""


class ParserRemitoAnthropic(PuertoParserRemitoVision):
    def __init__(self) -> None:
        cfg = obtener_configuracion()
        if not cfg.anthropic_api_key:
            raise ReglaDeNegocioViolada(
                "Falta VENTAS360_ANTHROPIC_API_KEY para parsear remitos con IA"
            )
        self._client = Anthropic(api_key=cfg.anthropic_api_key)
        self._model = cfg.anthropic_model
        self._max_tokens = cfg.anthropic_max_tokens

    async def parsear(self, contenido: bytes, media_type: str) -> RemitoExtraido:
        b64 = base64.standard_b64encode(contenido).decode("ascii")
        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": b64,
                                },
                            },
                            {"type": "text", "text": PROMPT},
                        ],
                    }
                ],
            )
        except Exception as exc:
            raise ReglaDeNegocioViolada(
                "No se pudo analizar la imagen con el servicio de IA"
            ) from exc

        texto = ""
        for block in response.content:
            if block.type == "text":
                texto += block.text
        if not texto.strip():
            raise ReglaDeNegocioViolada("El modelo no devolvió texto interpretable")
        data = parsear_json_modelo(texto)
        return remito_desde_json(data)
