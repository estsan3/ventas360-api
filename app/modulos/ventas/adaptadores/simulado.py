"""Adaptador SIMULADO de WSFE: CAE ficticio con formato real, sin red."""

import random
from datetime import date

from app.modulos.ventas.fiscal import vencimiento_cae
from app.modulos.ventas.puerto import ProveedorFE, ResultadoFE, SolicitudFE


class AdaptadorSimulado(ProveedorFE):
    """Autoriza siempre, salvo importes o documentos evidentemente inválidos."""

    async def ultimo_autorizado(
        self, *, cuit_emisor: str, punto_venta: int, cbte_tipo: int
    ) -> int:
        return 0

    async def solicitar_cae(self, solicitud: SolicitudFE) -> ResultadoFE:
        if solicitud.imp_total <= 0:
            return ResultadoFE(autorizada=False, error="El importe total debe ser mayor a cero")
        if solicitud.cbte_nro < 1:
            return ResultadoFE(autorizada=False, error="Número de comprobante inválido")
        if solicitud.doc_tipo == 80 and len(solicitud.doc_nro) != 11:
            return ResultadoFE(autorizada=False, error="CUIT del receptor inválido")
        cae = f"{random.randint(10**13, 10**14 - 1)}"
        return ResultadoFE(
            autorizada=True,
            cae=cae,
            cae_vencimiento=vencimiento_cae(solicitud.fecha or date.today()),
            cbte_nro=solicitud.cbte_nro,
        )
