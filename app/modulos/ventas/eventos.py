"""Suscripciones a eventos de dominio del módulo ventas."""

from app.core.eventos import BusEventos, EventoDominio


async def _on_remito_confirmado(evento: EventoDominio) -> None:
    """Hook local: el egreso de stock ya ocurrió en la misma TX del service.

    Otros módulos (cxc, reportería) pueden suscribirse a este evento.
    """
    return None


async def _on_factura_creada(evento: EventoDominio) -> None:
    """Hook para imputación CxC (Fase A6)."""
    return None


def registrar_suscripciones_ventas(bus: BusEventos) -> None:
    bus.suscribir("ventas.remito.confirmado", _on_remito_confirmado)
    bus.suscribir("ventas.factura.creada", _on_factura_creada)
