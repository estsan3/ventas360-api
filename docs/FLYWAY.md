# Flyway — producto Ventas (schema `ventas`)

Fuente de verdad de **cómo** versionamos DDL. Flyway **no** corre dentro del proceso de la API: Pre-Deploy / CI / `scripts/flyway-migrate.sh`.

`create_all` de SQLAlchemy **sigue activo** (PR-A). El DDL de negocio se mueve a Flyway en PRs posteriores.

## Decisiones (no reabrir)

| Tema | Valor |
|------|--------|
| Database | `appdb` (una instancia Postgres por ambiente) |
| Schema de producto | `ventas` (`flyway.schemas=ventas`; historial **dentro** del schema) |
| URL | **sin** schema. `search_path=ventas` lo setea el rol |
| Roles | `ventas_migrator` (DDL / Flyway) y `ventas_app` (DML / API) |
| Tablas | se **conservan** los prefijos ORM (`ventas_pedido`, `clientes_cliente`, …) |
| Undo | no. No agregar `U__*.sql` |
| SQL de migración | **sin** prefijo `ventas.` (`CREATE TABLE ventas_pedido`, no `ventas.ventas_pedido`) |
| Secrets | solo env (`FLYWAY_*`, passwords de roles) |

Aislamiento futuro (no en este PR): producto → schema+rol; cliente → `tenant_id` uuid + RLS.

## Layout

```
flyway/conf/flyway.conf
flyway/sql/V1__baseline.sql          # marcador; sin DDL de negocio
scripts/bootstrap-roles.sh           # DB appdb + roles + search_path + default privileges
scripts/sql/bootstrap-roles.sql
scripts/flyway-migrate.sh            # FLYWAY_CMD local o Docker
```

## Local

Postgres del compose (`localhost:5433`, superuser `ventas360` / db `ventas360` para la app de siempre). Flyway usa **otra** DB: `appdb`.

```bash
docker compose up -d db

# 1) roles + schema ventas
./scripts/bootstrap-roles.sh

# 2) migrate (Docker; o FLYWAY_CMD=flyway ./scripts/flyway-migrate.sh)
./scripts/flyway-migrate.sh

# 3) verificar historial
docker compose exec -T db \
  psql -U ventas360 -d appdb -c "SELECT installed_rank, version, description, success FROM ventas.flyway_schema_history;"
```

Equivalente con profile Compose (no levanta api/web):

```bash
docker compose up -d db
docker compose --profile flyway run --rm flyway-bootstrap
docker compose --profile flyway run --rm flyway
```

Passwords locales por defecto: `ventas_migrator` / `ventas_app`. Override: `VENTAS_MIGRATOR_PASSWORD`, `VENTAS_APP_PASSWORD`.

## Render (Pre-Deploy)

1. Crear Postgres (`appdb-stage` / `appdb-prod`), database `appdb`.
2. Correr `bootstrap-roles.sh` **una vez** como admin de Render (crear roles con passwords de secretos).
3. Secrets del servicio API / job de migrate:
   - `FLYWAY_URL=jdbc:postgresql://<host>:5432/appdb?sslmode=require`
   - `FLYWAY_USER=ventas_migrator`
   - `FLYWAY_PASSWORD=…`
   - API: `VENTAS360_DATABASE_URL=postgresql+asyncpg://ventas_app:…@<host>:5432/appdb` (sin schema)
4. Pre-Deploy: `./scripts/flyway-migrate.sh` con `FLYWAY_CMD` apuntando al CLI, o un one-off con la imagen `flyway/flyway:11`. **No** meter Flyway en el request path de FastAPI.

## Siguientes PRs (no mezclar acá)

1. **PR-B** — pool por env + apagar `create_all` / seed en prod
2. **PR-C** — `tenant_id` uuid + índices `(tenant_id, …)`
3. **PR-D** — RLS ENABLE+FORCE + `set_config('app.tenant_id', $1, true)` al checkout del pool
4. **PR-E** — Cloudflare R2 (nada en disco del contenedor)
5. **PR-F** — worker IA async + metering por `tenant_id` (opcional día 1; si no, flag sync off)

Después: contratar Render (solo `ventas-prod` + stage Suspend).
