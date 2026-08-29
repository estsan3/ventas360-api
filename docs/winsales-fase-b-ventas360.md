# Fase B — Ventas360 (post núcleo comercial)

Fase A (A1–A9) cerrada. Esta fase amplía compras, tesorería y fiscal.

## Slices

| Slice | Alcance | Estado |
|-------|---------|--------|
| **B1** Proveedores + compras | Maestro, lista ≠ catálogo, pedido (OC), remito parcial, factura + CxP | Hecho (API + web) |
| **B2** Caja / medios | Caja diaria, vínculo con cobranzas | Hecho (API + web) |
| **B3** Bancos / valores | Cuentas bancarias, cheques/valores livianos | Hecho (API + web) |
| **B4** AFIP real | Puerto WSAA/WSFE + adaptador (simulado por default; `afip` con cert) | Hecho (API + web) |
| **B5** Fuerza de ventas / logística | Vendedores, zonas, hoja de ruta (solo si el negocio lo pide) | Pendiente |
| **B6** ETL WinSales | Migración `.mdb` (proyecto aparte) | Pendiente |

## B1 — Criterios de aceptación

- [x] CRUD proveedores (paginado).
- [x] Lista del proveedor persistida al importar Excel; **no** crea el catálogo. Alta/vínculo con SKU propio.
- [x] Pedido de compra (OC): borrador → emitir. No mueve stock ni CxP.
- [x] Remito de compra (también parcial contra un pedido) → confirmar ingresa stock.
- [x] Factura de compra: directa (stock + CxP) o desde remito (solo CxP, sin duplicar stock).
- [x] Consultar saldo CxP por proveedor (`GET /cxp/...`).
- [x] Web: `/compras` (pedidos, remitos/facturas, proveedores, listas).
- [x] Sin pagos a proveedor, sin contabilidad, sin AFIP.

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

Contabilidad operativa, taller completo, mensajería interna, NC/ND fiscales, alícuotas por producto.

## B4 — ARCA / factura electrónica

- [x] Identidad fiscal del emisor en parámetros (CUIT, condición IVA, PDV, domicilio).
- [x] Puerto WSAA/WSFE + adaptadores `simulado` y `afip` (mismo patrón que Agro360 CPE).
- [x] Al confirmar factura: letra A/B/C, CAE, vencimiento, número ARCA y QR.
- [x] Si ARCA rechaza, la factura no pasa a confirmado.
- [x] Web: Configuración → ARCA; mostrador muestra letra y CAE.

## Siguiente slice sugerido

**B5** fuerza de ventas / logística (solo si el negocio lo pide).
