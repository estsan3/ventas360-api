"""Contrato público del módulo bancos."""

from datetime import date
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.excepciones import RecursoNoEncontrado
from app.modulos.bancos.bo import BancosBO
from app.modulos.bancos.dao import BancosDAO
from app.modulos.bancos.models import MovimientoBancario, ValorBancario


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

    async def recibir_cheque(
        self,
        monto: float,
        numero: str,
        banco_emisor: str,
        librador: str = "",
        fecha: date | None = None,
        fecha_vto: date | None = None,
        recibido_de: str = "",
        origen: str = "",
        origen_id: str = "",
        observacion: str = "",
    ) -> str: ...

    async def entregar_cheque(
        self,
        valor_id: str,
        destinatario: str,
        fecha: date | None = None,
    ) -> None: ...

    async def emitir_cheque_propio(
        self,
        monto: float,
        numero: str,
        banco_emisor: str,
        destinatario: str,
        fecha: date | None = None,
        fecha_vto: date | None = None,
        observacion: str = "",
    ) -> str: ...


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

    async def recibir_cheque(
        self,
        monto: float,
        numero: str,
        banco_emisor: str,
        librador: str = "",
        fecha: date | None = None,
        fecha_vto: date | None = None,
        recibido_de: str = "",
        origen: str = "",
        origen_id: str = "",
        observacion: str = "",
    ) -> str:
        self._bo.validar_cheque(numero, banco_emisor, monto)
        valor = ValorBancario(
            tipo="cheque_tercero",
            estado="en_cartera",
            monto=round(monto, 2),
            fecha=fecha or date.today(),
            fecha_vto=fecha_vto,
            numero=numero.strip(),
            librador=(librador or recibido_de).strip()[:120],
            banco_emisor=banco_emisor.strip(),
            recibido_de=(recibido_de or librador).strip()[:120],
            origen=origen[:20],
            origen_id=origen_id[:36],
            observacion=observacion[:200],
        )
        await self._dao.guardar_valor(valor)
        return valor.id

    async def entregar_cheque(
        self,
        valor_id: str,
        destinatario: str,
        fecha: date | None = None,
    ) -> None:
        valor = await self._dao.buscar_valor(valor_id)
        if valor is None:
            raise RecursoNoEncontrado("Cheque no encontrado")
        self._bo.validar_entrega(valor.estado)
        self._bo.validar_destinatario(destinatario)
        valor.estado = "entregado"
        valor.entregado_a = destinatario.strip()[:120]
        valor.fecha_entrega = fecha or date.today()
        await self._dao.guardar_valor(valor)

    async def emitir_cheque_propio(
        self,
        monto: float,
        numero: str,
        banco_emisor: str,
        destinatario: str,
        fecha: date | None = None,
        fecha_vto: date | None = None,
        observacion: str = "",
    ) -> str:
        self._bo.validar_cheque(numero, banco_emisor, monto)
        self._bo.validar_destinatario(destinatario)
        dia = fecha or date.today()
        valor = ValorBancario(
            tipo="cheque_propio",
            estado="entregado",
            monto=round(monto, 2),
            fecha=dia,
            fecha_vto=fecha_vto,
            numero=numero.strip(),
            librador="Propio",
            banco_emisor=banco_emisor.strip(),
            entregado_a=destinatario.strip()[:120],
            fecha_entrega=dia,
            origen="caja",
            observacion=observacion[:200],
        )
        await self._dao.guardar_valor(valor)
        return valor.id
