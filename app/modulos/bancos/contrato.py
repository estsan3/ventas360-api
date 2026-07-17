"""Contrato público del módulo bancos."""

from datetime import date
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.excepciones import RecursoNoEncontrado
from app.modulos.bancos.bo import BancosBO
from app.modulos.bancos.dao import BancosDAO
from app.modulos.bancos.models import MovimientoBancario


class ContratoBancos(Protocol):
    async def acreditar(
        self,
        monto: float,
        concepto: str,
        referencia_tipo: str,
        referencia_id: str,
        cuenta_id: str | None = None,
        fecha: date | None = None,
    ) -> None: ...

    async def debitar(
        self,
        monto: float,
        concepto: str,
        referencia_tipo: str,
        referencia_id: str,
        cuenta_id: str | None = None,
        fecha: date | None = None,
    ) -> None: ...


class BancosLocal:
    """Sin commit: lo controla el service orquestador."""

    def __init__(self, sesion: AsyncSession) -> None:
        self._dao = BancosDAO(sesion)
        self._bo = BancosBO()

    async def acreditar(
        self,
        monto: float,
        concepto: str,
        referencia_tipo: str,
        referencia_id: str,
        cuenta_id: str | None = None,
        fecha: date | None = None,
    ) -> None:
        await self._registrar(
            "credito",
            monto,
            concepto,
            referencia_tipo,
            referencia_id,
            cuenta_id,
            fecha,
        )

    async def debitar(
        self,
        monto: float,
        concepto: str,
        referencia_tipo: str,
        referencia_id: str,
        cuenta_id: str | None = None,
        fecha: date | None = None,
    ) -> None:
        await self._registrar(
            "debito",
            monto,
            concepto,
            referencia_tipo,
            referencia_id,
            cuenta_id,
            fecha,
        )

    async def _registrar(
        self,
        tipo: str,
        monto: float,
        concepto: str,
        referencia_tipo: str,
        referencia_id: str,
        cuenta_id: str | None,
        fecha: date | None,
    ) -> None:
        self._bo.validar_movimiento(tipo, monto)
        if await self._dao.existe_referencia_mov(referencia_tipo, referencia_id):
            return

        cuenta = None
        if cuenta_id:
            cuenta = await self._dao.buscar_cuenta(cuenta_id)
        else:
            cuenta = await self._dao.buscar_cuenta_default()
        if cuenta is None or not cuenta.activo:
            raise RecursoNoEncontrado("Cuenta bancaria no encontrada")

        await self._dao.guardar_movimiento(
            MovimientoBancario(
                cuenta_id=cuenta.id,
                fecha=fecha or date.today(),
                tipo=tipo,
                monto=round(monto, 2),
                concepto=concepto,
                referencia_tipo=referencia_tipo,
                referencia_id=referencia_id,
            )
        )
