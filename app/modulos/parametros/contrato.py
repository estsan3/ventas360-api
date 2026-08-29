"""Contrato público del módulo parámetros."""

from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.excepciones import RecursoNoEncontrado
from app.core.tenant_ctx import tenant_id_actual
from app.modulos.parametros.bo import ParametrosBO
from app.modulos.parametros.dao import ParametrosDAO
from app.modulos.parametros.schemas import ParametrosAfip, ParametrosNegocio

_DEFAULTS = ParametrosNegocio(iva_porcentaje=21.0, moneda="ARS")
_DEFAULTS_AFIP = ParametrosAfip()


class ContratoParametros(Protocol):
    """Interfaz que parámetros garantiza al resto del sistema."""

    async def obtener_negocio(self) -> ParametrosNegocio: ...

    async def obtener_afip(self) -> ParametrosAfip: ...

    async def asignar_numero(self, tipo_comprobante: str) -> str: ...


class ParametrosLocal:
    """Implementación local: asignar_numero no hace commit."""

    def __init__(self, sesion: AsyncSession) -> None:
        self._dao = ParametrosDAO(sesion)
        self._bo = ParametrosBO()

    async def obtener_negocio(self) -> ParametrosNegocio:
        valores = await self._dao.obtener_todos(tenant_id_actual())
        return ParametrosNegocio(
            iva_porcentaje=float(
                valores.get("iva_porcentaje", _DEFAULTS.iva_porcentaje)
            ),
            moneda=valores.get("moneda", _DEFAULTS.moneda),  # type: ignore[arg-type]
        )

    async def obtener_afip(self) -> ParametrosAfip:
        valores = await self._dao.obtener_todos(tenant_id_actual())
        condicion = valores.get("afip_condicion_iva", _DEFAULTS_AFIP.condicion_iva)
        if condicion not in {
            "responsable_inscripto",
            "monotributo",
            "exento",
        }:
            condicion = _DEFAULTS_AFIP.condicion_iva
        try:
            punto = int(valores.get("afip_punto_venta", str(_DEFAULTS_AFIP.punto_venta)))
        except ValueError:
            punto = _DEFAULTS_AFIP.punto_venta
        return ParametrosAfip(
            habilitada=valores.get("afip_habilitada", "false").lower() == "true",
            cuit=valores.get("afip_cuit", ""),
            razon_social=valores.get("afip_razon_social", ""),
            condicion_iva=condicion,  # type: ignore[arg-type]
            punto_venta=punto,
            domicilio=valores.get("afip_domicilio", ""),
        )

    async def asignar_numero(self, tipo_comprobante: str) -> str:
        talonario = await self._dao.buscar_talonario_por_tipo(
            tenant_id_actual(), tipo_comprobante
        )
        if talonario is None or not talonario.activo:
            raise RecursoNoEncontrado(
                f"No hay talonario activo para {tipo_comprobante}"
            )
        numero = self._bo.formatear_numero(talonario.prefijo, talonario.proximo_numero)
        talonario.proximo_numero += 1
        await self._dao.guardar_talonario(talonario)
        return numero
