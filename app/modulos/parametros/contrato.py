"""Contrato público del módulo parámetros."""

from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.excepciones import RecursoNoEncontrado
from app.modulos.parametros.bo import ParametrosBO
from app.modulos.parametros.dao import ParametrosDAO
from app.modulos.parametros.schemas import ParametrosNegocio

_DEFAULTS = ParametrosNegocio(iva_porcentaje=21.0, moneda="ARS")


class ContratoParametros(Protocol):
    """Interfaz que parámetros garantiza al resto del sistema."""

    async def obtener_negocio(self) -> ParametrosNegocio: ...

    async def asignar_numero(self, tipo_comprobante: str) -> str: ...


class ParametrosLocal:
    """Implementación local: asignar_numero no hace commit."""

    def __init__(self, sesion: AsyncSession) -> None:
        self._dao = ParametrosDAO(sesion)
        self._bo = ParametrosBO()

    async def obtener_negocio(self) -> ParametrosNegocio:
        valores = await self._dao.obtener_todos()
        return ParametrosNegocio(
            iva_porcentaje=float(
                valores.get("iva_porcentaje", _DEFAULTS.iva_porcentaje)
            ),
            moneda=valores.get("moneda", _DEFAULTS.moneda),  # type: ignore[arg-type]
        )

    async def asignar_numero(self, tipo_comprobante: str) -> str:
        talonario = await self._dao.buscar_talonario_por_tipo(tipo_comprobante)
        if talonario is None or not talonario.activo:
            raise RecursoNoEncontrado(
                f"No hay talonario activo para {tipo_comprobante}"
            )
        numero = self._bo.formatear_numero(talonario.prefijo, talonario.proximo_numero)
        talonario.proximo_numero += 1
        await self._dao.guardar_talonario(talonario)
        return numero
