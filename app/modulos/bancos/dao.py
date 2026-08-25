"""DAO del módulo bancos."""

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant_ctx import del_tenant, es_del_tenant
from app.modulos.bancos.models import CuentaBancaria, MovimientoBancario, ValorBancario


class BancosDAO:
    def __init__(self, sesion: AsyncSession) -> None:
        self._sesion = sesion

    async def listar_cuentas(self, solo_activas: bool = True) -> list[CuentaBancaria]:
        consulta = (
            select(CuentaBancaria)
            .where(del_tenant(CuentaBancaria))
            .order_by(CuentaBancaria.codigo)
        )
        if solo_activas:
            consulta = consulta.where(CuentaBancaria.activo.is_(True))
        return list((await self._sesion.execute(consulta)).scalars())

    async def buscar_cuenta(self, cuenta_id: str) -> CuentaBancaria | None:
        cuenta = await self._sesion.get(CuentaBancaria, cuenta_id)
        return cuenta if es_del_tenant(cuenta) else None

    async def buscar_cuenta_default(self) -> CuentaBancaria | None:
        resultado = await self._sesion.execute(
            select(CuentaBancaria).where(
                del_tenant(CuentaBancaria),
                CuentaBancaria.es_default.is_(True),
                CuentaBancaria.activo.is_(True),
            )
        )
        return resultado.scalar_one_or_none()

    async def guardar_cuenta(self, cuenta: CuentaBancaria) -> CuentaBancaria:
        self._sesion.add(cuenta)
        await self._sesion.flush()
        return cuenta

    async def guardar_movimiento(
        self, mov: MovimientoBancario
    ) -> MovimientoBancario:
        self._sesion.add(mov)
        await self._sesion.flush()
        return mov

    async def listar_movimientos(
        self, cuenta_id: str | None = None
    ) -> list[MovimientoBancario]:
        consulta = (
            select(MovimientoBancario)
            .where(del_tenant(MovimientoBancario))
            .order_by(
                MovimientoBancario.fecha.desc(), MovimientoBancario.creado_en.desc()
            )
        )
        if cuenta_id:
            consulta = consulta.where(MovimientoBancario.cuenta_id == cuenta_id)
        return list((await self._sesion.execute(consulta)).scalars())

    async def existe_referencia_mov(
        self, referencia_tipo: str, referencia_id: str
    ) -> bool:
        if not referencia_id:
            return False
        resultado = await self._sesion.execute(
            select(func.count())
            .select_from(MovimientoBancario)
            .where(
                del_tenant(MovimientoBancario),
                MovimientoBancario.referencia_tipo == referencia_tipo,
                MovimientoBancario.referencia_id == referencia_id,
            )
        )
        return int(resultado.scalar_one()) > 0

    async def totales_cuenta(self, cuenta_id: str) -> tuple[float, float]:
        resultado = await self._sesion.execute(
            select(
                func.coalesce(
                    func.sum(
                        case(
                            (
                                MovimientoBancario.tipo == "credito",
                                MovimientoBancario.monto,
                            ),
                            else_=0.0,
                        )
                    ),
                    0.0,
                ),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                MovimientoBancario.tipo == "debito",
                                MovimientoBancario.monto,
                            ),
                            else_=0.0,
                        )
                    ),
                    0.0,
                ),
            ).where(
                del_tenant(MovimientoBancario),
                MovimientoBancario.cuenta_id == cuenta_id,
            )
        )
        creditos, debitos = resultado.one()
        return float(creditos), float(debitos)

    async def listar_valores(
        self, estado: str | None = None
    ) -> list[ValorBancario]:
        consulta = (
            select(ValorBancario)
            .where(del_tenant(ValorBancario))
            .order_by(ValorBancario.fecha.desc())
        )
        if estado:
            consulta = consulta.where(ValorBancario.estado == estado)
        return list((await self._sesion.execute(consulta)).scalars())

    async def buscar_valor(self, valor_id: str) -> ValorBancario | None:
        valor = await self._sesion.get(ValorBancario, valor_id)
        return valor if es_del_tenant(valor) else None

    async def guardar_valor(self, valor: ValorBancario) -> ValorBancario:
        self._sesion.add(valor)
        await self._sesion.flush()
        return valor
