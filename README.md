# Ventas360 API

Backend modular de **Ventas360**: administración de ventas y comercio retail con soporte para agentes de IA (MCP).

Monolito FastAPI organizado en módulos autónomos (`auth`, `clientes`, `productos`, `ventas`, `parametros`, `reporteria`) listos para extraerse como microservicios.

## Comandos

```bash
poetry install
poetry run uvicorn app.main:app --reload   # http://localhost:8000
poetry run pytest
poetry run ruff check . --fix
poetry run python -m scripts.seed
```

## Login demo

- Email: `admin@ventas360.com`
- Contraseña: `demo12345`

Docs interactivas: [http://localhost:8000/docs](http://localhost:8000/docs)

## Configuración

Variables con prefijo `VENTAS360_` (ver `.env.example`):

| Variable | Default |
|----------|---------|
| `VENTAS360_DATABASE_URL` | SQLite local |
| `VENTAS360_SEED_AL_INICIAR` | `true` |
| `VENTAS360_MCP_HABILITADO` | `false` |

## Arquitectura

Cada módulo sigue: `router → service → bo + dao + models + schemas` (+ `contrato.py` si otros módulos lo consumen).

Reglas clave: commit solo en service, IDs débiles entre módulos, tablas con prefijo (`ventas_`, `clientes_`, `productos_`), errores de negocio tipados.

Ver `AGENTS.md` para la guía completa de convenciones.

## Análisis WinSales → módulos

Documentación derivada de `WINSALES.mdb` (inventario de módulos y priorización):

- [Validación de uso real (taller / contabilidad / OC)](docs/winsales-validacion-modulos.md)
- [Plan Fase A sobre Ventas360](docs/winsales-fase-a-ventas360.md)

## MCP (agentes IA)

```bash
poetry install --with mcp
VENTAS360_MCP_HABILITADO=true poetry run uvicorn app.main:app
```

Servidor MCP en `/mcp` con nombre **Ventas360**.
