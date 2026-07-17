"""Suscripciones a eventos de dominio del módulo ventas.

Registrar en `main.py` vía `registrar_suscripciones_ventas()`.
Hoy no hay efectos secundarios locales; el archivo deja el gancho listo
para stock/cxc cuando se implementen (Fase A).
"""

from app.core.eventos import BusEventos, EventoDominio


async def _log_pedido_creado(evento: EventoDominio) -> None:
    """Placeholder: otros módulos se suscriben a `ventas.pedido.creado`."""
    return None


def registrar_suscripciones_ventas(bus: BusEventos) -> None:
    """Registra manejadores propios de ventas (si aplica)."""
    bus.suscribir("ventas.pedido.creado", _log_pedido_creado)
