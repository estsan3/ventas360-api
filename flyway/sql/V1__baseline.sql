-- Marcador de baseline del schema ventas.
-- DDL de negocio no va acá: create_all sigue activo.
-- Las tablas conservan prefijo de módulo (ventas_pedido, clientes_cliente, …).

DO $$
BEGIN
  RAISE NOTICE 'Flyway V1 baseline (schema ventas)';
END $$;
