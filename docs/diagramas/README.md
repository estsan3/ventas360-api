# Diagramas de secuencia — Ventas360 API

Cada módulo tiene un diagrama del **flujo principal** (no el CRUD de listar).
Las capas siguen `router → service → BO + DAO`; el **commit** ocurre solo en el service.
La comunicación entre módulos es por `contrato.py` (síncrona) o `EventoDominio` (asíncrona).

Prefijo HTTP: `/api/v1`. Actualizado: **2026-08-26**.

## Cómo mantenerlos

Al cambiar `router.py`, `service.py`, `contrato.py` o `eventos.py` de un módulo, actualizar el `.md` correspondiente y la fecha de esta tabla. Si se agrega un módulo, crear `docs/diagramas/<nombre>.md` y una fila acá (ver `AGENTS.md`).

## Índice

| Módulo | Flujo principal | Archivo |
|--------|-----------------|---------|
| *(transversal)* | Request autenticado + tenant + capas | [00-transversal.md](00-transversal.md) |
| *(cadena)* | Remito → CxC → recibo → tesorería | [cadena-venta-cobro.md](cadena-venta-cobro.md) |
| auth | Login (Host + JWT cookie) | [auth.md](auth.md) |
| tenants | Crear comercio + admin inicial | [tenants.md](tenants.md) |
| clientes | Alta de cliente | [clientes.md](clientes.md) |
| zonas | Alta de zona | [zonas.md](zonas.md) |
| productos | Alta de producto (sync stock) | [productos.md](productos.md) |
| precios | Upsert precio de artículo | [precios.md](precios.md) |
| stock | Ajuste de saldo | [stock.md](stock.md) |
| ventas | Confirmar remito | [ventas.md](ventas.md) |
| cxc | `registrar_debe` (contrato) | [cxc.md](cxc.md) |
| cobranzas | Crear recibo | [cobranzas.md](cobranzas.md) |
| proveedores | Importar lista Excel | [proveedores.md](proveedores.md) |
| compras | Confirmar compra | [compras.md](compras.md) |
| cxp | `registrar_debe` (contrato) | [cxp.md](cxp.md) |
| caja | Ingreso (contrato + HTTP) | [caja.md](caja.md) |
| bancos | Acreditar + depositar valor | [bancos.md](bancos.md) |
| parametros | Guardar negocio | [parametros.md](parametros.md) |
| reporteria | KPIs del dashboard | [reporteria.md](reporteria.md) |
