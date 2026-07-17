# Validación de módulos WinSales (uso real en WINSALES.mdb)

Fecha de análisis: 2026-07-16  
Fuente: `~/Desktop/WINSALES.mdb` (conteos vía `mdb-export`)

Objetivo: decidir si **taller**, **contabilidad** y **órdenes de compra** se priorizan, se postergan o se descartan en un sucesor moderno (Ventas360), basándose en el uso real de la base — no solo en la existencia de tablas.

## Resumen ejecutivo

| Área | Uso en esta BD | Decisión recomendada |
|------|----------------|----------------------|
| Taller / reparaciones | Parcial (turnos/colocaciones con datos; órdenes de reparación vacías) | **Fase C / opcional** — no bloquear el núcleo |
| Contabilidad | Solo maestros; sin asientos ni movimientos | **Descartar del MVP** — Fase C si el negocio lo pide |
| Órdenes de compra | Casi nulo (OC = 0; compras mínimas) | **No Fase A** — compras livianas en Fase B |
| Núcleo comercial | Muy alto (remitos, facturas, cobranzas, catálogo) | **Fase A obligatoria** |

---

## 1. Taller / reparaciones

| Tabla | Filas | Interpretación |
|------:|------:|----------------|
| `OrdenRepar` | 0 | Órdenes formales no usadas |
| `ItemsOrdRepar` | 0 | Sin ítems de OR |
| `Reparaciones` | 84 | Catálogo / historial liviano |
| `Turnos` | 25 | Agenda usada de forma limitada |
| `TurnosColocaciones` | 398 | Actividad de colocaciones no despreciable |

**Conclusión:** hay señal de servicio/colocaciones, pero **no** un flujo de taller completo (sin órdenes de reparación).  
**Acción:** no implementar en Fase A. Incluir en Fase C solo si el negocio confirma colocaciones/turnos como proceso. Mientras tanto: **descartable para el core ERP de ventas**.

---

## 2. Contabilidad

| Tabla | Filas | Interpretación |
|------:|------:|----------------|
| `PlanCuentas` | 264 | Plan cargado (maestro) |
| `CentroCostos` | 2 | Casi vacío |
| `AsientosTipo` / `AsientosAuto` / `AsiAutoma` | 3 / 10 / 10 | Configuración mínima |
| `Asientos` | 0 | Sin asientos operativos |
| `MovContables` / `MovContabHisto` | 0 / 0 | Sin movimientos |
| `AsientosHisto` / `AsientosBorra` | 0 / 0 | Sin historial |

**Conclusión:** la contabilidad está **preparada pero no operada** en este dump (o se lleva afuera).  
**Acción:** **fuera de Fase A y B**. Reevaluar en Fase C; hasta entonces se asume contabilidad externa o diferida.

---

## 3. Órdenes de compra y compras

| Tabla | Filas | Interpretación |
|------:|------:|----------------|
| `OrdenesCpra` / `ItemsOrdCompra` | 0 / 0 | OC no usadas |
| `PedidosCompra` / `ItemsPedCompra` | 6 / 8 | Pedidos a proveedor residuales |
| `facturasCompra` / `Itemscompra` | 38 / 63 | Compras esporádicas |
| `PresuCpras` | 0 | Sin presupuestos de compra |
| `Proveedores` | 33 | Maestro chico vs 2.691 clientes |

**Conclusión:** el negocio de esta base es **venta/distribución**, no compra intensiva. Las OC formales se pueden **descartar del alcance inicial**; facturas/remitos de compra bastan en Fase B si hace falta reposición.

**Acción:** OC → no implementar hasta demanda explícita. Compras mínimas → Fase B.

---

## 4. Contraste: módulos con uso fuerte (no descartar)

| Tabla | Filas | Rol |
|------:|------:|-----|
| `Articulos` | 194.833 | Catálogo |
| `RemitosVenta` / `ItemsRemito` | 41.172 / 87.355 | Documento operativo dominante |
| `FacturasVenta` / `ItemsVenta` | 13.667 / 77.709 | Facturación (+ CAE) |
| `RecibosCli` | 11.494 | Cobranza |
| `Clientes` | 2.691 | Cartera |
| `Remarcaciones` | 43.406 | Precios / márgenes |
| `CuentaCorriente` | 254 | CxC (movimientos; saldos pueden estar en otros lados) |
| `Depositos` | 168 | Multi-depósito |
| `CAJA` / `Bancos` | 24 / 55 | Caja y bancos livianos |
| `PedidosVenta` | 2 | Pedidos formales casi no usados |

**Nota:** `ListasPrecios*` tiene pocas filas, pero `Remarcaciones` es masiva → el motor de precios existe; modelarlo en Fase A vía listas/remarcación simplificada.

**Logística / fuerza de ventas en esta BD:** `HojadeRuta` = 0; `Choferes`/`Transportes`/`Vendedores`/`Cobradores` ≈ 1 fila cada uno → maestros mínimos; Fase B solo si el negocio lo usa fuera de este dump.

---

## 5. Decisiones cerradas para Ventas360

1. **Incluir en Fase A:** auth, parámetros, clientes, artículos, precios/remarcación, stock multi-depósito, ventas (remito + factura; pedido opcional), CxC, cobranzas, reportería básica.  
2. **Postergar (Fase B):** compras sin OC, caja/medios, bancos, fiscal/AFIP profundo, vendedores/zonas, logística.  
3. **Descartar o Fase C:** contabilidad operativa, OC formales, taller completo, mensajería interna.  
4. **Validación humana restante (opcional):** confirmar si `TurnosColocaciones` es proceso del día a día; si sí, un mini-módulo “colocaciones” en Fase C.

Ver plan de implementación: [winsales-fase-a-ventas360.md](./winsales-fase-a-ventas360.md).
