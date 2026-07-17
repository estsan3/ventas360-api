"""SERVICE del módulo parámetros."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.excepciones import RecursoNoEncontrado, ReglaDeNegocioViolada
from app.modulos.parametros.bo import ParametrosBO
from app.modulos.parametros.dao import ParametrosDAO
from app.modulos.parametros.models import Talonario
from app.modulos.parametros.schemas import (
    NumeroAsignadoResponse,
    ParametrosNegocio,
    ParametrosOperativos,
    PreferenciasNotificacion,
    TalonarioResponse,
    UpsertTalonarioRequest,
)

_DEFAULTS_NEGOCIO = ParametrosNegocio(iva_porcentaje=21.0, moneda="ARS")
_DEFAULTS_OPERATIVOS = ParametrosOperativos()
_DEFAULTS_PREFERENCIAS = PreferenciasNotificacion(
    stock_bajo=True, venta_confirmada=True, cliente_nuevo=True
)


class ParametrosService:
    """Casos de uso de configuración global."""

    def __init__(self, sesion: AsyncSession) -> None:
        self._sesion = sesion
        self._dao = ParametrosDAO(sesion)
        self._bo = ParametrosBO()

    async def obtener_negocio(self) -> ParametrosNegocio:
        valores = await self._dao.obtener_todos()
        return ParametrosNegocio(
            iva_porcentaje=float(
                valores.get("iva_porcentaje", _DEFAULTS_NEGOCIO.iva_porcentaje)
            ),
            moneda=valores.get("moneda", _DEFAULTS_NEGOCIO.moneda),  # type: ignore[arg-type]
        )

    async def guardar_negocio(self, datos: ParametrosNegocio) -> ParametrosNegocio:
        await self._dao.guardar_varios(
            {
                "iva_porcentaje": str(datos.iva_porcentaje),
                "moneda": datos.moneda,
            }
        )
        await self._sesion.commit()
        return datos

    async def obtener_operativos(self) -> ParametrosOperativos:
        valores = await self._dao.obtener_todos()
        condiciones_raw = valores.get(
            "condiciones_pago", ",".join(_DEFAULTS_OPERATIVOS.condiciones_pago)
        )
        condiciones = [c.strip() for c in condiciones_raw.split(",") if c.strip()]
        return ParametrosOperativos(
            sucursal_codigo=valores.get(
                "sucursal_codigo", _DEFAULTS_OPERATIVOS.sucursal_codigo
            ),
            sucursal_nombre=valores.get(
                "sucursal_nombre", _DEFAULTS_OPERATIVOS.sucursal_nombre
            ),
            condiciones_pago=condiciones or list(_DEFAULTS_OPERATIVOS.condiciones_pago),
        )

    async def guardar_operativos(
        self, datos: ParametrosOperativos
    ) -> ParametrosOperativos:
        if not datos.condiciones_pago:
            raise ReglaDeNegocioViolada("Debe haber al menos una condición de pago")
        await self._dao.guardar_varios(
            {
                "sucursal_codigo": datos.sucursal_codigo,
                "sucursal_nombre": datos.sucursal_nombre,
                "condiciones_pago": ",".join(datos.condiciones_pago),
            }
        )
        await self._sesion.commit()
        return datos

    async def obtener_preferencias(self) -> PreferenciasNotificacion:
        valores = await self._dao.obtener_todos()

        def _leer_bool(clave: str, default: bool) -> bool:
            return valores.get(clave, str(default)).lower() == "true"

        return PreferenciasNotificacion(
            stock_bajo=_leer_bool("notif_stock_bajo", True),
            venta_confirmada=_leer_bool("notif_venta_confirmada", True),
            cliente_nuevo=_leer_bool("notif_cliente_nuevo", True),
        )

    async def guardar_preferencias(
        self, datos: PreferenciasNotificacion
    ) -> PreferenciasNotificacion:
        await self._dao.guardar_varios(
            {
                "notif_stock_bajo": str(datos.stock_bajo),
                "notif_venta_confirmada": str(datos.venta_confirmada),
                "notif_cliente_nuevo": str(datos.cliente_nuevo),
            }
        )
        await self._sesion.commit()
        return datos

    async def listar_talonarios(self) -> list[TalonarioResponse]:
        items = await self._dao.listar_talonarios()
        return [TalonarioResponse.model_validate(t) for t in items]

    async def upsert_talonario(
        self, datos: UpsertTalonarioRequest
    ) -> TalonarioResponse:
        self._bo.validar_talonario(datos.tipo_comprobante, datos.proximo_numero)
        existente = await self._dao.buscar_talonario_por_tipo(datos.tipo_comprobante)
        if existente is None:
            existente = Talonario(tipo_comprobante=datos.tipo_comprobante)
        existente.prefijo = datos.prefijo
        existente.proximo_numero = datos.proximo_numero
        existente.activo = datos.activo
        await self._dao.guardar_talonario(existente)
        await self._sesion.commit()
        return TalonarioResponse.model_validate(existente)

    async def asignar_numero(self, tipo_comprobante: str) -> NumeroAsignadoResponse:
        """Reserva e incrementa el próximo número del talonario (sin commit)."""
        self._bo.validar_talonario(tipo_comprobante, 1)
        talonario = await self._dao.buscar_talonario_por_tipo(tipo_comprobante)
        if talonario is None or not talonario.activo:
            raise RecursoNoEncontrado(
                f"No hay talonario activo para {tipo_comprobante}"
            )
        numero = self._bo.formatear_numero(talonario.prefijo, talonario.proximo_numero)
        talonario.proximo_numero += 1
        await self._dao.guardar_talonario(talonario)
        return NumeroAsignadoResponse(tipo_comprobante=tipo_comprobante, numero=numero)
