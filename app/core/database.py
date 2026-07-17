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
    from app.modulos.bancos import models as _bancos_models  # noqa: F401
    from app.modulos.caja import models as _caja_models  # noqa: F401
    from app.modulos.clientes import models as _clientes_models  # noqa: F401
    from app.modulos.cobranzas import models as _cobranzas_models  # noqa: F401
    from app.modulos.compras import models as _compras_models  # noqa: F401
    from app.modulos.cxc import models as _cxc_models  # noqa: F401
    from app.modulos.cxp import models as _cxp_models  # noqa: F401
    from app.modulos.parametros import models as _parametros_models  # noqa: F401
    from app.modulos.precios import models as _precios_models  # noqa: F401
    from app.modulos.productos import models as _productos_models  # noqa: F401
    from app.modulos.proveedores import models as _proveedores_models  # noqa: F401
    from app.modulos.stock import models as _stock_models  # noqa: F401
    from app.modulos.ventas import models as _ventas_models  # noqa: F401
    from app.modulos.zonas import models as _zonas_models  # noqa: F401

    async with engine.begin() as conexion:
        await conexion.run_sync(Base.metadata.create_all)
        await conexion.run_sync(_asegurar_columnas_proveedores)


def _asegurar_columnas_proveedores(conexion) -> None:
    """Agrega columnas nuevas de listas Excel si la tabla ya existía."""
    from sqlalchemy import inspect, text

    inspector = inspect(conexion)
    if "proveedores_proveedor" not in inspector.get_table_names():
        return
    existentes = {col["name"] for col in inspector.get_columns("proveedores_proveedor")}
    dialecto = conexion.dialect.name
    extras: list[tuple[str, str]] = [
        ("mapeo_excel", "JSON" if dialecto == "postgresql" else "TEXT"),
        ("excel_fila_inicio", "INTEGER DEFAULT 2"),
        ("politica_precio_venta", "VARCHAR(40) DEFAULT 'solo_costo'"),
        ("margen_venta_pct", "FLOAT DEFAULT 30"),
        ("ultima_importacion_fecha", "TIMESTAMP"),
        ("ultima_importacion_archivo", "VARCHAR(255) DEFAULT ''"),
        ("ultima_importacion_actualizados", "INTEGER DEFAULT 0"),
        ("ultima_importacion_nuevos", "INTEGER DEFAULT 0"),
        ("ultima_importacion_sin_match", "INTEGER DEFAULT 0"),
    ]
    for nombre, tipo in extras:
        if nombre in existentes:
            continue
        conexion.execute(
            text(f"ALTER TABLE proveedores_proveedor ADD COLUMN {nombre} {tipo}")
        )
