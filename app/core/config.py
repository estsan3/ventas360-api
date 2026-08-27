"""Configuración central de la aplicación.

Todas las variables se leen del entorno (o de un archivo `.env`) con el
prefijo `VENTAS360_`. Ver `.env.example` en la raíz del repo.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Configuracion(BaseSettings):
    """Variables de configuración tipadas y validadas por Pydantic."""

    model_config = SettingsConfigDict(
        env_prefix="VENTAS360_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Entorno de ejecución: dev | test | prod
    entorno: str = "dev"

    # URL de conexión SQLAlchemy (async). SQLite en dev, PostgreSQL al escalar.
    database_url: str = "sqlite+aiosqlite:///./data/ventas360.db"

    # Seguridad / JWT
    jwt_secreto: str = "cambiar-este-secreto-en-produccion"
    jwt_algoritmo: str = "HS256"
    jwt_expiracion_minutos: int = 480

    # Orígenes permitidos para CORS, separados por coma (credentials → nunca *).
    cors_origins: str = "http://localhost:4200,http://localhost:4201"

    # Subdominios locales (`http://agronorte.localhost:4201`). Vacío = no usar regex.
    cors_origin_regex: str = r"https?://([a-z0-9-]+\.)?localhost:4201"

    # Primera etiqueta de host de la plataforma (admin.localhost, admin.midominio.com).
    slug_plataforma: str = "admin"

    # Sembrar datos de demo al iniciar si la base está vacía (solo dev).
    seed_al_iniciar: bool = True

    # Exponer la API como servidor MCP para agentes de IA.
    mcp_habilitado: bool = False

    # Parseo de remitos con visión (Claude Haiku).
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-haiku-4-5-20251001"
    anthropic_max_tokens: int = 4096
    # auto = Anthropic si hay API key; mock = datos demo; anthropic = forzar API.
    remito_parse_modo: str = "auto"
    remito_parse_max_mb: int = 5

    @property
    def cors_origins_lista(self) -> list[str]:
        """Devuelve los orígenes CORS como lista limpia."""
        return [origen.strip() for origen in self.cors_origins.split(",") if origen.strip()]

    @property
    def es_produccion(self) -> bool:
        return self.entorno == "prod"


@lru_cache
def obtener_configuracion() -> Configuracion:
    """Instancia única de configuración (cacheada para todo el proceso)."""
    return Configuracion()
