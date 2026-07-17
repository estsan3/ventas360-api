"""Capa SERVICE del módulo parámetros.

Módulo sin BO: los parámetros no tienen reglas de negocio más allá de la
validación de tipos, que ya la hacen los schemas Pydantic.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.modulos.parametros.dao import ParametrosDAO
from app.modulos.parametros.schemas import ParametrosNegocio, PreferenciasNotificacion

_DEFAULTS_NEGOCIO = ParametrosNegocio(iva_porcentaje=21.0, moneda="ARS")
_DEFAULTS_PREFERENCIAS = PreferenciasNotificacion(
    stock_bajo=True, venta_confirmada=True, cliente_nuevo=True
)


class ParametrosService:
    """Casos de uso de configuración global."""

    def __init__(self, sesion: AsyncSession) -> None:
        self._sesion = sesion
        self._dao = ParametrosDAO(sesion)

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
