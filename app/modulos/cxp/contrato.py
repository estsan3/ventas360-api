"""Contrato público CxP."""

from datetime import date
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.modulos.cxp.bo import CxpBO
from app.modulos.cxp.dao import CxpDAO
from app.modulos.cxp.models import MovimientoCxp


class ContratoCxp(Protocol):
    async def registrar_debe(
        self,
        proveedor_id: str,
        monto: float,
        referencia_tipo: str,
        referencia_id: str,
        concepto: str,
        fecha: date | None = None,
    ) -> None: ...

    async def registrar_haber(
        self,
        proveedor_id: str,
        monto: float,
        referencia_tipo: str,
        referencia_id: str,
        concepto: str,
        fecha: date | None = None,
    ) -> None: ...

    async def saldo_proveedor(self, proveedor_id: str) -> float: ...


class CxpLocal:
    """Sin commit: lo controla el service orquestador."""

    def __init__(self, sesion: AsyncSession) -> None:
        self._dao = CxpDAO(sesion)
        self._bo = CxpBO()

    async def registrar_debe(
        self,
        proveedor_id: str,
        monto: float,
        referencia_tipo: str,
        referencia_id: str,
        concepto: str,
        fecha: date | None = None,
    ) -> None:
        await self._registrar(
            "debe",
            proveedor_id,
            monto,
            referencia_tipo,
            referencia_id,
            concepto,
            fecha,
        )

    async def registrar_haber(
        self,
        proveedor_id: str,
        monto: float,
        referencia_tipo: str,
        referencia_id: str,
        concepto: str,
        fecha: date | None = None,
    ) -> None:
        await self._registrar(
            "haber",
            proveedor_id,
            monto,
            referencia_tipo,
            referencia_id,
            concepto,
            fecha,
        )

    async def saldo_proveedor(self, proveedor_id: str) -> float:
        debe, haber = await self._dao.totales_proveedor(proveedor_id)
        return self._bo.calcular_saldo(debe, haber)

    async def _registrar(
        self,
        tipo: str,
        proveedor_id: str,
        monto: float,
        referencia_tipo: str,
        referencia_id: str,
        concepto: str,
        fecha: date | None,
    ) -> None:
        self._bo.validar_movimiento(tipo, monto)
        if referencia_id and await self._dao.existe_referencia(
            referencia_tipo, referencia_id
        ):
            return
        await self._dao.guardar(
            MovimientoCxp(
                proveedor_id=proveedor_id,
                tipo=tipo,
                monto=round(monto, 2),
                referencia_tipo=referencia_tipo,
                referencia_id=referencia_id,
                concepto=concepto,
                fecha=fecha or date.today(),
            )
        )
