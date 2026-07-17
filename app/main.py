"""Punto de entrada de la API Ventas360.

Composición de la aplicación: registra los routers de cada módulo, los
handlers de errores y (opcionalmente) el servidor MCP para agentes de IA.

Ejecutar en desarrollo:
    poetry run uvicorn app.main:app --reload
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import obtener_configuracion
from app.core.database import crear_tablas
from app.core.eventos import bus_eventos
from app.core.excepciones import ErrorDeNegocio, manejar_error_de_negocio
from app.modulos.auth.router import router as auth_router
from app.modulos.auth.router import router_usuarios, router_vendedores
from app.modulos.bancos.router import router as bancos_router
from app.modulos.caja.router import router as caja_router
from app.modulos.clientes.router import router as clientes_router
from app.modulos.cobranzas.router import router as cobranzas_router
from app.modulos.compras.router import router as compras_router
from app.modulos.cxc.router import router as cxc_router
from app.modulos.cxp.router import router as cxp_router
from app.modulos.parametros.router import router as parametros_router
from app.modulos.precios.router import router as precios_router
from app.modulos.productos.router import router as productos_router
from app.modulos.proveedores.router import router as proveedores_router
from app.modulos.reporteria.router import router as reporteria_router
from app.modulos.stock.router import router as stock_router
from app.modulos.ventas.eventos import registrar_suscripciones_ventas
from app.modulos.ventas.router import router as ventas_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    """Inicialización al arrancar: tablas y seed de demo."""
    config = obtener_configuracion()

    await crear_tablas()

    if config.seed_al_iniciar and not config.es_produccion:
        from scripts.seed import sembrar_datos_demo

        await sembrar_datos_demo()

    logger.info("Ventas360 API iniciada (entorno: %s)", config.entorno)
    yield


def crear_aplicacion() -> FastAPI:
    """Fábrica de la aplicación FastAPI con todos los módulos registrados."""
    config = obtener_configuracion()

    app = FastAPI(
        title="Ventas360 API",
        description=(
            "Backend modular de Ventas360: administración de ventas y comercio "
            "con agentes de IA. Incluye Fase B1: proveedores, compras y CxP."
        ),
        version="0.1.0",
        lifespan=ciclo_de_vida,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins_lista,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(ErrorDeNegocio, manejar_error_de_negocio)  # type: ignore[arg-type]

    registrar_suscripciones_ventas(bus_eventos)

    prefijo = "/api/v1"
    app.include_router(auth_router, prefix=prefijo)
    app.include_router(router_usuarios, prefix=prefijo)
    app.include_router(router_vendedores, prefix=prefijo)
    app.include_router(clientes_router, prefix=prefijo)
    app.include_router(productos_router, prefix=prefijo)
    app.include_router(precios_router, prefix=prefijo)
    app.include_router(stock_router, prefix=prefijo)
    app.include_router(ventas_router, prefix=prefijo)
    app.include_router(cxc_router, prefix=prefijo)
    app.include_router(cobranzas_router, prefix=prefijo)
    app.include_router(proveedores_router, prefix=prefijo)
    app.include_router(compras_router, prefix=prefijo)
    app.include_router(cxp_router, prefix=prefijo)
    app.include_router(caja_router, prefix=prefijo)
    app.include_router(bancos_router, prefix=prefijo)
    app.include_router(parametros_router, prefix=prefijo)
    app.include_router(reporteria_router, prefix=prefijo)

    @app.get("/health", tags=["Infraestructura"], operation_id="health")
    async def health() -> dict[str, str]:
        """Chequeo de vida para orquestadores (Docker, Kubernetes)."""
        return {"status": "ok"}

    if config.mcp_habilitado:
        _montar_mcp(app)

    return app


def _montar_mcp(app: FastAPI) -> None:
    """Monta el servidor MCP en /mcp (requiere `poetry install --with mcp`)."""
    try:
        from fastapi_mcp import FastApiMCP

        mcp = FastApiMCP(app, name="Ventas360")
        mcp.mount()
        logger.info("Servidor MCP montado en /mcp")
    except ImportError:
        logger.warning(
            "VENTAS360_MCP_HABILITADO=true pero falta fastapi-mcp. "
            "Instalar con: poetry install --with mcp"
        )


app = crear_aplicacion()
