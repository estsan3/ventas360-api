# Guía para agentes de IA — Ventas360 API

Sos un agente de backend para **Ventas360 API** (FastAPI + SQLAlchemy 2.0 async + Pydantic + Poetry).
Trabajá en español: código, comentarios, docstrings y mensajes de error.
Seguí SIEMPRE estas reglas. Si una solicitud las viola, proponé el diseño correcto antes de implementar.

## Stack y contexto

- Python / FastAPI monolito modular (preparado para microservicios)
- SQLAlchemy 2.0 async, SQLite (dev) / PostgreSQL (prod)
- JWT + roles (cookie httpOnly y/o Bearer); errores de negocio unificados
- MCP opcional (`operation_id` en endpoints para tools de agentes)
- Repo: `ventas360-api` · Prefijo env: `VENTAS360_*`
- Esta guía (`AGENTS.md`) es la fuente de verdad del repo

## Mapa del código

- `app/core/`: config, DB, JWT, eventos, excepciones. **Sin lógica de negocio.**
- `app/modulos/<modulo>/`: un paquete por dominio con esta estructura:
  - `router.py` → HTTP (sin lógica)
  - `service.py` → casos de uso + **único lugar de commit**
  - `bo.py` → reglas puras (sin DB, sin HTTP, sin modelos ORM)
  - `dao.py` → persistencia (`flush()`, nunca `commit()`)
  - `models.py` → ORM (`Mapped[...]`)
  - `schemas.py` → DTOs `*Request` / `*Response`
  - `contrato.py` (opcional) → Protocol público para otros módulos
  - `eventos.py` (opcional) → suscripciones al bus de dominio
  - `puerto.py` + `adaptadores/` (opcional) → integraciones externas
- `scripts/seed.py`, `tests/`

## Reglas de arquitectura (OBLIGATORIAS)

1. **Nunca** importar service/bo/dao/models de un módulo desde otro. Solo vía `contrato.py`.
2. **Nunca** ForeignKey entre módulos distintos. IDs débiles (`String`) + validación por contrato.
3. Tablas con prefijo del módulo: `ventas_pedido`, `auth_usuario`, `clientes_cliente`, `productos_producto`.
4. **Commit solo en service.** DAO solo `flush()`.
5. BO puro: sin sesión DB, sin Request/Response, sin modelos ORM. Lanza excepciones de `app.core.excepciones`.
6. Router fino: recibe DTO → llama service → devuelve DTO.
7. Efectos entre módulos → `EventoDominio` en `app.core.eventos` (`modulo.entidad.accion`). Suscripciones en `eventos.py` del módulo oyente, registradas en `main.py`.
8. Integraciones externas (pagos, AFIP, ERP, etc.) detrás de puerto/adaptador; nunca llamadas directas desde service.

## Convenciones

- Español en nombres de dominio, mensajes y docs.
- Endpoints con `operation_id` en snake_case (`crear_pedido`).
- Errores: `RecursoNoEncontrado`, `ReglaDeNegocioViolada`, `NoAutenticado`, `NoAutorizado`
  → JSON `{"error": {"codigo", "mensaje"}}`.
- IDs: UUID4 en texto.
- Config tipada con Pydantic Settings (`VENTAS360_*`).
- No meter lógica de negocio en `core/`, ni SQL en routers, ni HTTP en BO.

## Al agregar un módulo

1. Crear `app/modulos/<nombre>/` (plantilla: `parametros` simple o `ventas` completa).
2. Prefijo tablas `<nombre>_`.
3. Registrar models en `crear_tablas()` (`app/core/database.py`) y router en `crear_aplicacion()` (`app/main.py`).
4. Exponer `contrato.py` si otros módulos lo necesitan.
5. Si publica/escucha eventos, agregar `eventos.py` y registrar suscripciones en `main.py`.
6. Tests: `tests/test_bo_<nombre>.py` + integración API.

## Buenas prácticas de implementación

- Cambios mínimos y alineados al estilo existente; no refactors colaterales.
- Tipado estricto; evitar `Any` innecesario.
- Validar reglas en BO; orquestar en service; persistir en DAO.
- Endpoints idempotentes cuando aplique; mensajes de error claros para UI.
- Tras cambios: `poetry run ruff check . --fix` y `poetry run pytest` en lo afectado.
- No inventar endpoints ni campos “por las dudas”; pedir aclaración si falta requisito.

## Forma de trabajar

1. Leé módulos vecinos antes de escribir.
2. Proponé el diseño en 2–4 bullets si el cambio toca arquitectura.
3. Implementá respetando capas.
4. Agregá/ajustá tests del BO o flujo API.
5. Resumen breve de qué cambió y cómo probarlo.

## Comandos

```bash
poetry install
poetry run uvicorn app.main:app --reload
poetry run pytest
poetry run ruff check . --fix
poetry run python -m scripts.seed
```

## Demo

Login: `admin@ventas360.com` / `demo12345` · Docs: `/docs` · Health: `/health`
