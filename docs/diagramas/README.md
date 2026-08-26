# Diagramas de secuencia — Ventas360 API

Fuente de verdad: el código en `app/modulos/` (router → service → BO/DAO/contratos).
Estos diagramas se regeneran cuando cambia un módulo. Prefijo HTTP global: `/api/v1`.

**Última sincronización:** 2026-08-26 (módulos en `app/main.py`).

## Convenciones

- Capas: `Router` (HTTP) → `Service` (commit) → `BO` (reglas) / `DAO` (flush) / `Contrato*` (otros módulos).
- Flecha sólida `->>`: llamada sincrónica. Punteada `-->>`: respuesta.
- Eventos de dominio: `modulo.entidad.accion`, publicados **después** del commit.
- IDs débiles entre módulos: no hay FK; la validación pasa por `contrato.py`.
- Todo endpoint de comercio (salvo login/contexto) pasa antes por [flujo transversal](00-transversal.md).

## Índice

| Módulo | Flujo principal | Diagrama |
|--------|-----------------|----------|
| Transversal | JWT + Host + tenant + permisos | [00-transversal.md](00-transversal.md) |
| auth | Login por Host | [auth.md](auth.md) |
| tenants | Alta de comercio (plataforma) | [tenants.md](tenants.md) |
| clientes | Alta de cliente | [clientes.md](clientes.md) |
| zonas | Alta de zona | [zonas.md](zonas.md) |
| productos | Alta de producto + stock inicial | [productos.md](productos.md) |
| precios | Upsert precio de lista | [precios.md](precios.md) |
| stock | Ajuste de inventario | [stock.md](stock.md) |
| ventas | Confirmar remito (stock + CxC) | [ventas.md](ventas.md) |
| cxc | Debe vía contrato (desde ventas) | [cxc.md](cxc.md) |
| cobranzas | Crear recibo (CxC + tesorería) | [cobranzas.md](cobranzas.md) |
| proveedores | Importar lista Excel | [proveedores.md](proveedores.md) |
| compras | Confirmar compra (stock + CxP) | [compras.md](compras.md) |
| cxp | Debe vía contrato (desde compras) | [cxp.md](cxp.md) |
| caja | Ingreso vía contrato (desde cobranzas) | [caja.md](caja.md) |
| bancos | Acreditar vía contrato / depositar valor | [bancos.md](bancos.md) |
| parametros | Guardar negocio + talonario | [parametros.md](parametros.md) |
| reporteria | KPIs del dashboard | [reporteria.md](reporteria.md) |
| Cadena | Remito → factura → recibo | [cadena-venta-cobro.md](cadena-venta-cobro.md) |

## Cómo mantenerlos actualizados

1. Si cambia `router.py`, `service.py`, `contrato.py` o `eventos.py` de un módulo, actualizar **ese** `.md`.
2. Si se agrega un módulo: crear `docs/diagramas/<nombre>.md`, linkearlo acá y en `AGENTS.md`.
3. El flujo transversal se actualiza si cambian `tenants/dependencias.py`, `core/seguridad.py` o `core/dependencias.py`.
4. No inventar pasos: el diagrama debe coincidir con funciones reales.
