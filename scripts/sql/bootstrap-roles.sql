-- Bootstrap del schema ventas y privilegios.
-- Corre como superusuario / owner de la DB, conectado a `appdb`.
-- Los roles ventas_migrator / ventas_app ya deben existir (los crea bootstrap-roles.sh).
-- Idempotente. SQL sin prefijo de schema en objetos de negocio.

CREATE SCHEMA IF NOT EXISTS ventas AUTHORIZATION ventas_migrator;
ALTER SCHEMA ventas OWNER TO ventas_migrator;

GRANT USAGE, CREATE ON SCHEMA ventas TO ventas_migrator;
GRANT USAGE ON SCHEMA ventas TO ventas_app;
REVOKE CREATE ON SCHEMA ventas FROM ventas_app;
REVOKE ALL ON SCHEMA ventas FROM PUBLIC;

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA ventas TO ventas_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA ventas TO ventas_app;

ALTER DEFAULT PRIVILEGES FOR ROLE ventas_migrator IN SCHEMA ventas
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO ventas_app;

ALTER DEFAULT PRIVILEGES FOR ROLE ventas_migrator IN SCHEMA ventas
  GRANT USAGE, SELECT ON SEQUENCES TO ventas_app;
