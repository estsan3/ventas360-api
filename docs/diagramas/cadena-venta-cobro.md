# Cadena venta → cobro → tesorería

Fuente: `ventas`, `cxc`, `cobranzas`, `caja`, `bancos`, `stock`, `parametros`.
Actualizado: 2026-08-28.

Flujo de punta a punta de un remito de venta hasta el impacto en caja, banco o cartera de cheques. Cada paso HTTP es un caso de uso con su propia transacción, salvo el impacto interno vía contrato (misma TX que el service llamador).

```mermaid
sequenceDiagram
    participant Cliente
    participant Ventas as VentasService
    participant Stock as ContratoStock
    participant Cxc as ContratoCxc
    participant Cobranzas as CobranzasService
    participant Caja as ContratoCaja
    participant Bancos as ContratoBancos
    participant Bus as bus_eventos

    Cliente->>Ventas: POST /ventas/pedidos tipo remito
    Ventas->>Ventas: armar lineas, IVA, talonario
    Ventas-->>Cliente: remito borrador

    Cliente->>Ventas: POST /ventas/pedidos/{id}/confirmar-remito
    Ventas->>Stock: egresar por cada linea
    Ventas->>Cxc: registrar_debe referencia remito
    Ventas->>Ventas: commit
    Ventas-)Bus: ventas.remito.confirmado
    Ventas-->>Cliente: remito confirmado

    Cliente->>Ventas: POST /ventas/pedidos/{id}/facturar
    Ventas->>Cxc: existe_referencia remito
    Ventas->>Ventas: commit
    Ventas-)Bus: ventas.factura.creada
    Ventas-->>Cliente: factura confirmada

    Cliente->>Cobranzas: POST /cobranzas/recibos
    Cobranzas->>Cxc: registrar_haber monto del recibo
    loop cada linea de medio
        alt transferencia
            Cobranzas->>Bancos: acreditar
        else cheque
            Cobranzas->>Bancos: recibir_cheque en_cartera
            Cobranzas->>Caja: registrar_ingreso medio cheque
        else efectivo o tarjeta
            Cobranzas->>Caja: registrar_ingreso
        end
    end
    Cobranzas->>Cobranzas: commit
    Cobranzas-)Bus: cobranzas.recibo.creado
    Cobranzas-->>Cliente: ReciboResponse
```

Si el remito ya imputó CxC, facturar no duplica el debe.

El recibo puede imputar de menos (a cuenta) o nada (anticipo). Varios medios en un cobro quedan como `mixto`.

El espejo de compras es `compras.md` + `cxp.md` (ingreso de stock y debe al proveedor). El parseo de remito por foto está en `compras.md` (no crea la compra).
