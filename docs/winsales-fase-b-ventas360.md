# Fase B — Ventas360 (post núcleo comercial)

Fase A (A1–A9) cerrada. Esta fase amplía compras, tesorería y fiscal.

## Slices

| Slice | Alcance | Estado |
|-------|---------|--------|
| **B1** Proveedores + compras mínimas | Maestro proveedores, remito/factura de compra → ingreso stock + CxP | Hecho (API + web) |
| **B2** Caja / medios | Caja diaria, vínculo con cobranzas | Hecho (API + web) |
| **B3** Bancos / valores | Cuentas bancarias, cheques/valores livianos | Hecho (API + web) |
| **B4** AFIP real | Puerto WSAA/WSFE + adaptador (hoy solo placeholder CAE) | Pendiente |
| **B5** Fuerza de ventas / logística | Vendedores, zonas, hoja de ruta (solo si el negocio lo pide) | Pendiente |
| **B6** ETL WinSales | Migración `.mdb` (proyecto aparte) | Pendiente |

## B1 — Criterios de aceptación

- [x] CRUD proveedores (paginado).
- [x] Crear remito de compra y confirmar → ingresa stock al depósito.
- [x] Crear/confirmar factura de compra → ingresa stock (si aplica) e imputa CxP (debe).
- [x] Consultar saldo CxP por proveedor (`GET /cxp/...`).
- [x] Web: menú Proveedores + Compras con UI kit.
- [x] Sin OC formales, sin contabilidad.

## B2 — Caja / medios

- [x] Movimientos de caja (`ingreso` / `egreso`) por fecha + saldo del día.
- [x] Recibo en efectivo/tarjeta → ingreso de caja (vía contrato).
- [x] Alta manual de movimientos (admin).
- [x] Web: pantalla Caja con KPIs y tabla.

## B3 — Bancos / valores

- [x] Cuentas bancarias + saldo calculado.
- [x] Recibo por transferencia → crédito en cuenta default.
- [x] Valores (cheques) en cartera → depositar acredita banco.
- [x] Web: pantalla Bancos (cuentas + valores).

## Fuera de Fase B (Fase C / descartable)

Contabilidad operativa, OC formales, taller completo, mensajería interna.

## Siguiente slice sugerido

**B4 AFIP**: puerto WSAA/WSFE + adaptador; hoy solo campo `cae` placeholder en facturas.
