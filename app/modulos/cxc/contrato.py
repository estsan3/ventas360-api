"""Contrato público del módulo cxc."""

from datetime import date
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.modulos.cxc.bo import CxcBO
from app.modulos.cxc.dao import CxcDAO
from app.modulos.cxc.models import MovimientoCxc


class ContratoCxc(Protocol):
    async def registrar_debe(
        self,
        cliente_id: str,
        monto: float,
        referencia_tipo: str,
        referencia_id: str,
        concepto: str,
        fecha: date | None = None,
    ) -> None: ...

    async def registrar_haber(
        self,
        cliente_id: str,
        monto: float,
        referencia_tipo: str,
        referencia_id: str,
        concepto: str,
        fecha: date | None = None,
    ) -> None: ...

    async def saldo_cliente(self, cliente_id: str) -> float: ...


class CxcLocal:
    """Implementación local: no hace commit (lo controla el service orquestador)."""

    def __init__(self, sesion: AsyncSession) -> None:
        self._dao = CxcDAO(sesion)
        self._bo = CxcBO()

    async def registrar_debe(
        self,
        cliente_id: str,
        monto: float,
        referencia_tipo: str,
        referencia_id: str,
        concepto: str,
        fecha: date | None = None,
    ) -> None:
        await self._registrar(
            "debe", cliente_id, monto, referencia_tipo, referencia_id, concepto, fecha
        )

    async def registrar_haber(
        self,
        cliente_id: str,
        monto: float,
        referencia_tipo: str,
        referencia_id: str,
        concepto: str,
        fecha: date | None = None,
    ) -> None:
        await self._registrar(
            "haber", cliente_id, monto, referencia_tipo, referencia_id, concepto, fecha
        )

    async def saldo_cliente(self, cliente_id: str) -> float:
        debe, haber = await self._dao.totales_cliente(cliente_id)
        return self._bo.calcular_saldo(debe, haber)

    async def _registrar(
        self,
        tipo: str,
        cliente_id: str,
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
            return  # idempotente
        await self._dao.guardar(
            MovimientoCxc(
                cliente_id=cliente_id,
                tipo=tipo,
                monto=round(monto, 2),
                referencia_tipo=referencia_tipo,
                referencia_id=referencia_id,
                concepto=concepto,
                fecha=fecha or date.today(),
            )
        )
