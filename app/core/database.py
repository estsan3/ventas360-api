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
    from app.modulos.pagos import models as _pagos_models  # noqa: F401
    from app.modulos.parametros import models as _parametros_models  # noqa: F401
    from app.modulos.precios import models as _precios_models  # noqa: F401
    from app.modulos.productos import models as _productos_models  # noqa: F401
    from app.modulos.proveedores import models as _proveedores_models  # noqa: F401
    from app.modulos.stock import models as _stock_models  # noqa: F401
    from app.modulos.tenants import models as _tenants_models  # noqa: F401
    from app.modulos.ventas import models as _ventas_models  # noqa: F401
    from app.modulos.zonas import models as _zonas_models  # noqa: F401

    async with engine.begin() as conexion:
        await conexion.run_sync(Base.metadata.create_all)
        await conexion.run_sync(_asegurar_columnas_productos)
        await conexion.run_sync(_asegurar_columnas_proveedores)
        await conexion.run_sync(_asegurar_columnas_compras)
        await conexion.run_sync(_asegurar_caja)
        await conexion.run_sync(_asegurar_bancos)


def _asegurar_columnas_productos(conexion) -> None:
    """SKU propio y código de proveedor son campos distintos."""
    from sqlalchemy import inspect, text

    inspector = inspect(conexion)
    if "productos_producto" not in inspector.get_table_names():
        return
    existentes = {col["name"] for col in inspector.get_columns("productos_producto")}
    extras: list[tuple[str, str]] = [
        ("codigo_proveedor", "VARCHAR(40) DEFAULT ''"),
        ("proveedor", "VARCHAR(120) DEFAULT ''"),
    ]
    for nombre, tipo in extras:
        if nombre in existentes:
            continue
        conexion.execute(text(f"ALTER TABLE productos_producto ADD COLUMN {nombre} {tipo}"))


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


def _asegurar_columnas_compras(conexion) -> None:
    """Pedido de compra, código de proveedor en líneas, recepción parcial."""
    from sqlalchemy import inspect, text

    inspector = inspect(conexion)
    if "compras_compra" in inspector.get_table_names():
        cols = {col["name"] for col in inspector.get_columns("compras_compra")}
        extras_compra: list[tuple[str, str]] = [
            ("fecha_entrega", "DATE"),
            ("observaciones", "VARCHAR(500) DEFAULT ''"),
        ]
        for nombre, tipo in extras_compra:
            if nombre in cols:
                continue
            conexion.execute(text(f"ALTER TABLE compras_compra ADD COLUMN {nombre} {tipo}"))
    if "compras_linea" not in inspector.get_table_names():
        return
    cols_linea = {col["name"] for col in inspector.get_columns("compras_linea")}
    if "codigo_proveedor" not in cols_linea:
        conexion.execute(
            text("ALTER TABLE compras_linea ADD COLUMN codigo_proveedor VARCHAR(40) DEFAULT ''")
        )


def _asegurar_caja(conexion) -> None:
    """Permite varios turnos el mismo día y asocia movimientos a la sesión."""
    from sqlalchemy import inspect, text

    inspector = inspect(conexion)
    dialecto = conexion.dialect.name
    if "caja_sesion" in inspector.get_table_names():
        if dialecto == "postgresql":
            conexion.execute(
                text("ALTER TABLE caja_sesion DROP CONSTRAINT IF EXISTS uq_caja_sesion_dia")
            )
        else:
            conexion.execute(text("DROP INDEX IF EXISTS uq_caja_sesion_dia"))
            _quitar_unique_sesion_sqlite(conexion)
    if "caja_movimiento" not in inspector.get_table_names():
        return
    existentes = {col["name"] for col in inspector.get_columns("caja_movimiento")}
    if "sesion_id" not in existentes:
        conexion.execute(
            text("ALTER TABLE caja_movimiento ADD COLUMN sesion_id VARCHAR(36) DEFAULT ''")
        )
    if "caja_sesion" not in inspector.get_table_names():
        return
    cols_sesion = {col["name"] for col in inspector.get_columns("caja_sesion")}
    extras_sesion: list[tuple[str, str]] = [
        ("cheques_esperado", "FLOAT"),
        ("cheques_contado", "FLOAT"),
        ("cheques_diferencia", "FLOAT"),
        ("tarjetas_esperado", "FLOAT"),
        ("tarjetas_contado", "FLOAT"),
        ("tarjetas_diferencia", "FLOAT"),
    ]
    for nombre, tipo in extras_sesion:
        if nombre in cols_sesion:
            continue
        conexion.execute(text(f"ALTER TABLE caja_sesion ADD COLUMN {nombre} {tipo}"))


def _quitar_unique_sesion_sqlite(conexion) -> None:
    """SQLite guarda UNIQUE(tenant, fecha) como autoindex; hay que recrear la tabla."""
    from sqlalchemy import inspect, text

    inspector = inspect(conexion)
    uniques = inspector.get_unique_constraints("caja_sesion")
    hay_unique_dia = any(
        set(u.get("column_names") or []) == {"tenant_id", "fecha"} for u in uniques
    )
    if not hay_unique_dia:
        return
    cols = [c["name"] for c in inspector.get_columns("caja_sesion")]
    lista = ", ".join(cols)
    conexion.execute(text("DROP TABLE IF EXISTS caja_sesion_tmp"))
    conexion.execute(text(f"CREATE TABLE caja_sesion_tmp AS SELECT {lista} FROM caja_sesion"))
    conexion.execute(text("DROP TABLE caja_sesion"))
    conexion.execute(text("ALTER TABLE caja_sesion_tmp RENAME TO caja_sesion"))
    conexion.execute(text("CREATE INDEX IF NOT EXISTS ix_caja_sesion_tenant_id ON caja_sesion (tenant_id)"))
    conexion.execute(text("CREATE INDEX IF NOT EXISTS ix_caja_sesion_fecha ON caja_sesion (fecha)"))


def _asegurar_bancos(conexion) -> None:
    """Campos de cartera: de quién se recibió y a quién se entregó."""
    from sqlalchemy import inspect, text

    inspector = inspect(conexion)
    if "bancos_valor" not in inspector.get_table_names():
        return
    existentes = {col["name"] for col in inspector.get_columns("bancos_valor")}
    extras: list[tuple[str, str]] = [
        ("recibido_de", "VARCHAR(120) DEFAULT ''"),
        ("entregado_a", "VARCHAR(120) DEFAULT ''"),
        ("fecha_entrega", "DATE"),
        ("origen", "VARCHAR(20) DEFAULT ''"),
        ("origen_id", "VARCHAR(36) DEFAULT ''"),
    ]
    for nombre, tipo in extras:
        if nombre in existentes:
            continue
        conexion.execute(text(f"ALTER TABLE bancos_valor ADD COLUMN {nombre} {tipo}"))
