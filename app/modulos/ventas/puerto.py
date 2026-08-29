"""Puerto hacia el proveedor de factura electrónica (WSFE / ARCA).

El service de ventas depende de esta interfaz, nunca del SOAP concreto.
Así se desarrolla con el adaptador simulado y se cambia a ARCA real
sin tocar las reglas de negocio.
"""

from dataclasses import dataclass
from datetime import date
from typing import Protocol


@dataclass(frozen=True)
class SolicitudFE:
    """Pedido de CAE ya validado (un comprobante)."""

    cuit_emisor: str
    punto_venta: int
    cbte_tipo: int
    cbte_nro: int
    concepto: int
    doc_tipo: int
    doc_nro: str
    fecha: date
    imp_total: float
    imp_neto: float
    imp_iva: float
    imp_tot_conc: float
    iva_id: int | None
    condicion_iva_receptor: int
    moneda: str = "PES"
    cotizacion: float = 1.0


@dataclass(frozen=True)
class ResultadoFE:
    """Respuesta normalizada del proveedor, sea real o simulado."""

    autorizada: bool
    cae: str | None = None
    cae_vencimiento: date | None = None
    cbte_nro: int | None = None
    error: str = ""


class ProveedorFE(Protocol):
    """Contrato que debe cumplir cualquier adaptador de facturación electrónica."""

    async def ultimo_autorizado(
        self, *, cuit_emisor: str, punto_venta: int, cbte_tipo: int
    ) -> int:
        """Último CbteNro autorizado para el PDV + tipo (0 si no hay ninguno)."""
        ...

    async def solicitar_cae(self, solicitud: SolicitudFE) -> ResultadoFE:
        """Solicita CAE (FECAESolicitar)."""
        ...
