"""Infraestructura de base de datos (SQLAlchemy 2.0 async).

Decisiones de diseño pensadas para la futura división en microservicios:

- Cada módulo declara sus tablas con un PREFIJO propio (ej: `ventas_pedido`,
  `clientes_cliente`, `productos_producto`), que actúa como "schema lógico"
  en SQLite. Al migrar a PostgreSQL, esos prefijos se convierten en schemas
  reales (`ventas.pedido`) y cada módulo puede llevarse sus tablas a una base
  propia sin tocar a los demás.
- Ningún DAO de un módulo consulta tablas de otro módulo: si necesita datos
  ajenos, los pide a través del contrato público del otro módulo.
"""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import obtener_configuracion


class Base(DeclarativeBase):
    """Base declarativa común para todos los modelos ORM del sistema."""


_config = obtener_configuracion()
engine = create_async_engine(_config.database_url, echo=False)
fabrica_sesiones = async_sessionmaker(engine, expire_on_commit=False)


async def obtener_sesion() -> AsyncIterator[AsyncSession]:
    """Dependencia FastAPI: abre una sesión por request y la cierra al final.

    El commit/rollback es responsabilidad de la capa service (que define
    los límites transaccionales de cada caso de uso).
    """
    async with fabrica_sesiones() as sesion:
        yield sesion


async def crear_tablas() -> None:
    """Crea todas las tablas declaradas. Para desarrollo con SQLite."""
    from app.modulos.auth import models as _auth_models  # noqa: F401
    from app.modulos.clientes import models as _clientes_models  # noqa: F401
    from app.modulos.parametros import models as _parametros_models  # noqa: F401
    from app.modulos.precios import models as _precios_models  # noqa: F401
    from app.modulos.productos import models as _productos_models  # noqa: F401
    from app.modulos.stock import models as _stock_models  # noqa: F401
    from app.modulos.ventas import models as _ventas_models  # noqa: F401

    async with engine.begin() as conexion:
        await conexion.run_sync(Base.metadata.create_all)
