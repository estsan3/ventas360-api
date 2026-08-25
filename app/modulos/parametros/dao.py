"""DAO del módulo parámetros."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modulos.parametros.models import Parametro, Talonario


class ParametrosDAO:
    """Persistencia clave/valor + talonarios (por tenant)."""

    def __init__(self, sesion: AsyncSession) -> None:
        self._sesion = sesion

    async def obtener_todos(self, tenant_id: str) -> dict[str, str]:
        resultado = await self._sesion.execute(
            select(Parametro).where(Parametro.tenant_id == tenant_id)
        )
        return {p.clave: p.valor for p in resultado.scalars()}

    async def guardar_varios(self, tenant_id: str, valores: dict[str, str]) -> None:
        for clave, valor in valores.items():
            resultado = await self._sesion.execute(
                select(Parametro).where(
                    Parametro.tenant_id == tenant_id, Parametro.clave == clave
                )
            )
            existente = resultado.scalar_one_or_none()
            if existente is None:
                self._sesion.add(
                    Parametro(tenant_id=tenant_id, clave=clave, valor=valor)
                )
            else:
                existente.valor = valor
        await self._sesion.flush()

    async def listar_talonarios(self, tenant_id: str) -> list[Talonario]:
        resultado = await self._sesion.execute(
            select(Talonario)
            .where(Talonario.tenant_id == tenant_id)
            .order_by(Talonario.tipo_comprobante)
        )
        return list(resultado.scalars())

    async def buscar_talonario_por_tipo(
        self, tenant_id: str, tipo: str
    ) -> Talonario | None:
        resultado = await self._sesion.execute(
            select(Talonario).where(
                Talonario.tenant_id == tenant_id,
                Talonario.tipo_comprobante == tipo,
            )
        )
        return resultado.scalar_one_or_none()

    async def guardar_talonario(self, talonario: Talonario) -> Talonario:
        self._sesion.add(talonario)
        await self._sesion.flush()
        return talonario
