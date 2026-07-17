"""DAO del módulo parámetros."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modulos.parametros.models import Parametro, Talonario


class ParametrosDAO:
    """Persistencia clave/valor + talonarios."""

    def __init__(self, sesion: AsyncSession) -> None:
        self._sesion = sesion

    async def obtener_todos(self) -> dict[str, str]:
        resultado = await self._sesion.execute(select(Parametro))
        return {p.clave: p.valor for p in resultado.scalars()}

    async def guardar_varios(self, valores: dict[str, str]) -> None:
        for clave, valor in valores.items():
            existente = await self._sesion.get(Parametro, clave)
            if existente is None:
                self._sesion.add(Parametro(clave=clave, valor=valor))
            else:
                existente.valor = valor
        await self._sesion.flush()

    async def listar_talonarios(self) -> list[Talonario]:
        resultado = await self._sesion.execute(
            select(Talonario).order_by(Talonario.tipo_comprobante)
        )
        return list(resultado.scalars())

    async def buscar_talonario_por_tipo(self, tipo: str) -> Talonario | None:
        resultado = await self._sesion.execute(
            select(Talonario).where(Talonario.tipo_comprobante == tipo)
        )
        return resultado.scalar_one_or_none()

    async def guardar_talonario(self, talonario: Talonario) -> Talonario:
        self._sesion.add(talonario)
        await self._sesion.flush()
        return talonario
