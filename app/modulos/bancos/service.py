"""Service del módulo bancos."""

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.excepciones import RecursoNoEncontrado, ReglaDeNegocioViolada
from app.modulos.bancos.bo import BancosBO
from app.modulos.bancos.dao import BancosDAO
from app.modulos.bancos.models import CuentaBancaria, MovimientoBancario, ValorBancario
from app.modulos.bancos.schemas import (
    CrearCuentaBancariaRequest,
    CrearValorRequest,
    CuentaBancariaResponse,
    DepositarValorRequest,
    MovimientoBancarioResponse,
    ValorBancarioResponse,
)


class BancosService:
    def __init__(self, sesion: AsyncSession) -> None:
        self._sesion = sesion
        self._dao = BancosDAO(sesion)
        self._bo = BancosBO()

    async def listar_cuentas(self) -> list[CuentaBancariaResponse]:
        cuentas = await self._dao.listar_cuentas(solo_activas=False)
        result: list[CuentaBancariaResponse] = []
        for c in cuentas:
            creditos, debitos = await self._dao.totales_cuenta(c.id)
            resp = CuentaBancariaResponse.model_validate(c)
            resp.saldo = self._bo.calcular_saldo(creditos, debitos)
            result.append(resp)
        return result

    async def crear_cuenta(
        self, datos: CrearCuentaBancariaRequest
    ) -> CuentaBancariaResponse:
        if datos.es_default:
            await self._quitar_default()
        cuenta = CuentaBancaria(
            codigo=datos.codigo.strip().upper(),
            nombre=datos.nombre.strip(),
            banco=datos.banco,
            cbu=datos.cbu,
            es_default=datos.es_default,
        )
        await self._dao.guardar_cuenta(cuenta)
        await self._sesion.commit()
        resp = CuentaBancariaResponse.model_validate(cuenta)
        resp.saldo = 0.0
        return resp

    async def listar_movimientos(
        self, cuenta_id: str | None = None
    ) -> list[MovimientoBancarioResponse]:
        items = await self._dao.listar_movimientos(cuenta_id=cuenta_id)
        return [MovimientoBancarioResponse.model_validate(m) for m in items]

    async def listar_valores(
        self, estado: str | None = None
    ) -> list[ValorBancarioResponse]:
        items = await self._dao.listar_valores(estado=estado)
        return [ValorBancarioResponse.model_validate(v) for v in items]

    async def crear_valor(self, datos: CrearValorRequest) -> ValorBancarioResponse:
        self._bo.validar_valor(datos.tipo, datos.monto)
        valor = ValorBancario(
            tipo=datos.tipo,
            estado="en_cartera",
            monto=round(datos.monto, 2),
            fecha=datos.fecha or date.today(),
            fecha_vto=datos.fecha_vto,
            numero=datos.numero,
            librador=datos.librador,
            banco_emisor=datos.banco_emisor,
            observacion=datos.observacion,
        )
        await self._dao.guardar_valor(valor)
        await self._sesion.commit()
        return ValorBancarioResponse.model_validate(valor)

    async def depositar_valor(
        self, valor_id: str, datos: DepositarValorRequest
    ) -> ValorBancarioResponse:
        valor = await self._dao.buscar_valor(valor_id)
        if valor is None:
            raise RecursoNoEncontrado("Valor no encontrado")
        self._bo.validar_deposito(valor.estado)

        cuenta = None
        if datos.cuenta_id:
            cuenta = await self._dao.buscar_cuenta(datos.cuenta_id)
        else:
            cuenta = await self._dao.buscar_cuenta_default()
        if cuenta is None or not cuenta.activo:
            raise ReglaDeNegocioViolada("No hay cuenta bancaria destino activa")

        valor.estado = "depositado"
        valor.cuenta_destino_id = cuenta.id
        await self._dao.guardar_movimiento(
            MovimientoBancario(
                cuenta_id=cuenta.id,
                fecha=date.today(),
                tipo="credito",
                monto=valor.monto,
                concepto=f"Depósito valor {valor.numero or valor.id[:8]}",
                referencia_tipo="valor",
                referencia_id=valor.id,
            )
        )
        await self._dao.guardar_valor(valor)
        await self._sesion.commit()
        return ValorBancarioResponse.model_validate(valor)

    async def _quitar_default(self) -> None:
        for c in await self._dao.listar_cuentas(solo_activas=False):
            if c.es_default:
                c.es_default = False
                await self._dao.guardar_cuenta(c)
