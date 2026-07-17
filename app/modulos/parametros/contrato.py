"""Contrato público del módulo parámetros."""

from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.modulos.parametros.dao import ParametrosDAO
from app.modulos.parametros.schemas import ParametrosNegocio

_DEFAULTS = ParametrosNegocio(iva_porcentaje=21.0, moneda="ARS")


class ContratoParametros(Protocol):
    """Interfaz que parámetros garantiza al resto del sistema."""

    async def obtener_negocio(self) -> ParametrosNegocio: ...


class ParametrosLocal:
    """Implementación local del contrato (mismo proceso, misma base)."""

    def __init__(self, sesion: AsyncSession) -> None:
        self._dao = ParametrosDAO(sesion)

    async def obtener_negocio(self) -> ParametrosNegocio:
        valores = await self._dao.obtener_todos()
        return ParametrosNegocio(
            iva_porcentaje=float(
                valores.get("iva_porcentaje", _DEFAULTS.iva_porcentaje)
            ),
            moneda=valores.get("moneda", _DEFAULTS.moneda),  # type: ignore[arg-type]
        )
