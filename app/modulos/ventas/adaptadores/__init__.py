"""Adaptadores concretos del puerto ProveedorFE."""

from app.core.config import obtener_configuracion
from app.modulos.ventas.adaptadores.afip import AdaptadorAfip
from app.modulos.ventas.adaptadores.simulado import AdaptadorSimulado
from app.modulos.ventas.puerto import ProveedorFE


def crear_proveedor_fe() -> ProveedorFE:
    """Elige el adaptador según `VENTAS360_AFIP_PROVEEDOR` (simulado | afip)."""
    cfg = obtener_configuracion()
    if cfg.afip_proveedor.strip().lower() == "afip":
        return AdaptadorAfip.desde_config(cfg)
    return AdaptadorSimulado()
