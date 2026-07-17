"""Contrato público del módulo caja."""

from datetime import date
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.modulos.caja.bo import CajaBO
from app.modulos.caja.dao import CajaDAO
from app.modulos.caja.models import MovimientoCaja


class ContratoCaja(Protocol):
    async def registrar_ingreso(
        self,
        monto: float,
        medio: str,
        concepto: str,
        referencia_tipo: str,
        referencia_id: str,
        fecha: date | None = None,
    ) -> None: ...

    async def registrar_egreso(
        self,
        monto: float,
        medio: str,
        concepto: str,
        referencia_tipo: str,
        referencia_id: str,
        fecha: date | None = None,
    ) -> None: ...


class CajaLocal:
    """Sin commit: lo controla el service orquestador."""

    def __init__(self, sesion: AsyncSession) -> None:
        self._dao = CajaDAO(sesion)
        self._bo = CajaBO()

    async def registrar_ingreso(
        self,
        monto: float,
        medio: str,
        concepto: str,
        referencia_tipo: str,
        referencia_id: str,
        fecha: date | None = None,
    ) -> None:
        await self._registrar(
            "ingreso", monto, medio, concepto, referencia_tipo, referencia_id, fecha
        )

    async def registrar_egreso(
        self,
        monto: float,
        medio: str,
        concepto: str,
        referencia_tipo: str,
        referencia_id: str,
        fecha: date | None = None,
    ) -> None:
        await self._registrar(
            "egreso", monto, medio, concepto, referencia_tipo, referencia_id, fecha
        )

    async def _registrar(
        self,
        tipo: str,
        monto: float,
        medio: str,
        concepto: str,
        referencia_tipo: str,
        referencia_id: str,
        fecha: date | None,
    ) -> None:
        self._bo.validar_movimiento(tipo, medio, monto)
        if await self._dao.existe_referencia(referencia_tipo, referencia_id):
            return
        await self._dao.guardar(
            MovimientoCaja(
                fecha=fecha or date.today(),
                tipo=tipo,
                medio=medio,
                monto=round(monto, 2),
                concepto=concepto,
                referencia_tipo=referencia_tipo,
                referencia_id=referencia_id,
            )
        )
