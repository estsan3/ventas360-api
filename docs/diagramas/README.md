# Diagramas de secuencia — Ventas360 API

Cada módulo tiene un diagrama del **flujo principal** (no el CRUD de listar).
Las capas siguen `router → service → BO + DAO`; el **commit** ocurre solo en el service.
La comunicación entre módulos es por `contrato.py` (síncrona) o `EventoDominio` (asíncrona).

Prefijo HTTP: `/api/v1`. Actualizado: **2026-08-30**.

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
| stock | Ajuste de saldo + toma de inventario | [stock.md](stock.md) |
| ventas | Confirmar remito | [ventas.md](ventas.md) |
| cxc | `registrar_debe` (contrato) | [cxc.md](cxc.md) |
| cobranzas | Crear recibo | [cobranzas.md](cobranzas.md) |
| proveedores | Importar lista Excel (sin crear catálogo) | [proveedores.md](proveedores.md) |
| compras | Pedido → remito → factura | [compras.md](compras.md) |
| cxp | `registrar_debe` (contrato) | [cxp.md](cxp.md) |
| pagos | Pago a proveedor (CxP + tesorería) | [pagos.md](pagos.md) |
| caja | Ingreso, cheques y cierre por medio | [caja.md](caja.md) |
| bancos | Acreditar, cartera de cheques y depositar | [bancos.md](bancos.md) |
| parametros | Guardar negocio | [parametros.md](parametros.md) |
| reporteria | KPIs del dashboard | [reporteria.md](reporteria.md) |
| ia | Interpretar mostrador + resumen / webhook n8n | [ia.md](ia.md) |
