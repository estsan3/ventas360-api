"""Service del módulo caja."""

from datetime import UTC, date, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.excepciones import RecursoNoEncontrado
from app.modulos.bancos.contrato import BancosLocal
from app.modulos.bancos.dao import BancosDAO
from app.modulos.caja.bo import CajaBO
from app.modulos.caja.dao import CajaDAO
from app.modulos.caja.models import MovimientoCaja, SesionCaja
from app.modulos.caja.schemas import (
    AbrirCajaRequest,
    CerrarCajaRequest,
    CrearMovimientoCajaRequest,
    MovimientoCajaResponse,
    SaldoCajaResponse,
)


class CajaService:
    def __init__(self, sesion: AsyncSession) -> None:
        self._sesion = sesion
        self._dao = CajaDAO(sesion)
        self._bo = CajaBO()
        self._bancos = BancosLocal(sesion)
        self._bancos_dao = BancosDAO(sesion)

    async def listar_movimientos(
        self, dia: date | None = None
    ) -> list[MovimientoCajaResponse]:
        fecha = dia or date.today()
        items = await self._dao.listar_por_fecha(fecha)
        return [MovimientoCajaResponse.model_validate(m) for m in items]

    async def saldo(self, dia: date | None = None) -> SaldoCajaResponse:
        fecha = dia or date.today()
        ingresos, egresos = await self._dao.totales_fecha(fecha)
        caja = await self._dao.buscar_vigente(fecha)
        estado = "sin_abrir"
        if caja is not None:
            estado = "abierta" if caja.estado == "abierta" else "cerrada"
        efectivo = await self._esperado(fecha, "efectivo")
        cheques = await self._esperado(fecha, "cheque")
        tarjetas = await self._esperado(fecha, "tarjeta")
        return SaldoCajaResponse(
            fecha=fecha,
            ingresos=round(ingresos, 2),
            egresos=round(egresos, 2),
            saldo=self._bo.calcular_saldo(ingresos, egresos),
            efectivo_esperado=efectivo,
            estado=estado,
            fondo_inicial=caja.fondo_inicial if caja else 0,
            efectivo_contado=caja.efectivo_contado if caja else None,
            diferencia=caja.diferencia if caja else None,
            cheques_esperado=cheques,
            cheques_contado=caja.cheques_contado if caja else None,
            cheques_diferencia=caja.cheques_diferencia if caja else None,
            tarjetas_esperado=tarjetas,
            tarjetas_contado=caja.tarjetas_contado if caja else None,
            tarjetas_diferencia=caja.tarjetas_diferencia if caja else None,
            abierta_por=caja.abierta_por if caja else "",
            cerrada_por=caja.cerrada_por if caja else "",
            abierta_en=caja.abierta_en if caja else None,
            cerrada_en=caja.cerrada_en if caja else None,
        )

    async def abrir(
        self, datos: AbrirCajaRequest, abierta_por: str
    ) -> SaldoCajaResponse:
        fecha = datos.fecha or date.today()
        self._bo.validar_fondo(datos.fondo_inicial)
        existente = await self._dao.buscar_abierta(fecha)
        self._bo.validar_apertura(existente)
        caja = SesionCaja(
            fecha=fecha,
            estado="abierta",
            fondo_inicial=round(datos.fondo_inicial, 2),
            abierta_por=abierta_por[:120],
            abierta_en=datetime.now(UTC),
        )
        await self._dao.guardar_sesion(caja)
        if datos.fondo_inicial > 0:
            await self._dao.guardar(
                MovimientoCaja(
                    fecha=fecha,
                    tipo="ingreso",
                    medio="efectivo",
                    monto=round(datos.fondo_inicial, 2),
                    concepto="Fondo inicial",
                    referencia_tipo="apertura",
                    referencia_id=caja.id,
                    sesion_id=caja.id,
                )
            )
        await self._sesion.commit()
        return await self.saldo(fecha)

    async def cerrar(
        self, datos: CerrarCajaRequest, cerrada_por: str
    ) -> SaldoCajaResponse:
        fecha = datos.fecha or date.today()
        self._bo.validar_contado(datos.efectivo_contado, "efectivo contado")
        self._bo.validar_contado(datos.cheques_contado, "cheques contados")
        self._bo.validar_contado(datos.tarjetas_contado, "tarjetas contadas")
        caja = await self._dao.buscar_abierta(fecha)
        self._bo.validar_caja_abierta(caja)
        assert caja is not None
        esperado_ef = await self._esperado(fecha, "efectivo")
        esperado_ch = await self._esperado(fecha, "cheque")
        esperado_tj = await self._esperado(fecha, "tarjeta")
        caja.estado = "cerrada"
        caja.efectivo_esperado = esperado_ef
        caja.efectivo_contado = round(datos.efectivo_contado, 2)
        caja.diferencia = self._bo.calcular_diferencia(
            esperado_ef, caja.efectivo_contado
        )
        caja.cheques_esperado = esperado_ch
        caja.cheques_contado = round(datos.cheques_contado, 2)
        caja.cheques_diferencia = self._bo.calcular_diferencia(
            esperado_ch, caja.cheques_contado
        )
        caja.tarjetas_esperado = esperado_tj
        caja.tarjetas_contado = round(datos.tarjetas_contado, 2)
        caja.tarjetas_diferencia = self._bo.calcular_diferencia(
            esperado_tj, caja.tarjetas_contado
        )
        caja.cerrada_por = cerrada_por[:120]
        caja.cerrada_en = datetime.now(UTC)
        await self._sesion.commit()
        return await self.saldo(fecha)

    async def crear_movimiento(
        self, datos: CrearMovimientoCajaRequest
    ) -> MovimientoCajaResponse:
        self._bo.validar_movimiento(datos.tipo, datos.medio, datos.monto)
        fecha = datos.fecha or date.today()
        caja = await self._dao.buscar_abierta(fecha)
        self._bo.validar_caja_abierta(caja)
        assert caja is not None
        if datos.tipo == "egreso" and datos.medio == "efectivo":
            self._bo.validar_egreso_efectivo(
                datos.monto, await self._esperado(fecha, "efectivo")
            )
        concepto = (datos.concepto or "").strip()
        if datos.tipo == "egreso":
            self._bo.validar_concepto_egreso(concepto)
        referencia_tipo = "manual"
        referencia_id = ""
        if datos.medio == "cheque":
            referencia_tipo, referencia_id = await self._aplicar_cheque(datos, fecha)
        mov = MovimientoCaja(
            fecha=fecha,
            tipo=datos.tipo,
            medio=datos.medio,
            monto=round(datos.monto, 2),
            concepto=concepto or f"{datos.tipo} manual",
            referencia_tipo=referencia_tipo,
            referencia_id=referencia_id,
            sesion_id=caja.id,
        )
        await self._dao.guardar(mov)
        await self._sesion.commit()
        return MovimientoCajaResponse.model_validate(mov)

    async def _aplicar_cheque(
        self, datos: CrearMovimientoCajaRequest, fecha: date
    ) -> tuple[str, str]:
        self._bo.validar_datos_cheque(
            datos.tipo, datos.cheque_id, datos.cheque is not None
        )
        if datos.tipo == "ingreso":
            assert datos.cheque is not None
            valor_id = await self._bancos.recibir_cheque(
                monto=datos.monto,
                numero=datos.cheque.numero,
                banco_emisor=datos.cheque.banco_emisor,
                librador=datos.cheque.librador,
                fecha=datos.cheque.fecha or fecha,
                fecha_vto=datos.cheque.fecha_vto,
                recibido_de=datos.cheque.recibido_de or datos.cheque.librador,
                origen="caja",
                observacion=datos.concepto,
            )
            return "cheque", valor_id
        if datos.cheque_id:
            valor = await self._bancos_dao.buscar_valor(datos.cheque_id)
            if valor is None:
                raise RecursoNoEncontrado("Cheque no encontrado")
            self._bo.validar_monto_cheque(datos.monto, valor.monto)
            destinatario = (datos.entregado_a or "").strip()
            if datos.cheque and datos.cheque.destinatario:
                destinatario = datos.cheque.destinatario
            await self._bancos.entregar_cheque(
                datos.cheque_id, destinatario, fecha
            )
            return "cheque", datos.cheque_id
        assert datos.cheque is not None
        destinatario = (datos.entregado_a or datos.cheque.destinatario).strip()
        valor_id = await self._bancos.emitir_cheque_propio(
            monto=datos.monto,
            numero=datos.cheque.numero,
            banco_emisor=datos.cheque.banco_emisor,
            destinatario=destinatario,
            fecha=datos.cheque.fecha or fecha,
            fecha_vto=datos.cheque.fecha_vto,
            observacion=datos.concepto,
        )
        return "cheque", valor_id

    async def _esperado(self, dia: date, medio: str) -> float:
        ingresos, egresos = await self._dao.totales_fecha(dia, medio=medio)
        return self._bo.calcular_saldo(ingresos, egresos)
