"""Selección del adaptador de visión según configuración."""

from app.core.config import obtener_configuracion
from app.modulos.compras.adaptadores.anthropic import ParserRemitoAnthropic
from app.modulos.compras.adaptadores.mock import ParserRemitoMock
from app.modulos.compras.puerto import PuertoParserRemitoVision


def crear_parser_remito() -> PuertoParserRemitoVision:
    cfg = obtener_configuracion()
    modo = cfg.remito_parse_modo.lower()
    if modo == "mock":
        return ParserRemitoMock()
    if modo == "anthropic":
        return ParserRemitoAnthropic()
    # auto: Anthropic si hay key, si no mock (dev local)
    if cfg.anthropic_api_key:
        return ParserRemitoAnthropic()
    return ParserRemitoMock()
