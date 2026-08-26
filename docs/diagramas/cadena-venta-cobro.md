# Cadena extremo a extremo — remito → factura → recibo

Orquesta ventas, stock, CxC, cobranzas y tesorería. Cada service hace **su** commit; los contratos solo hacen flush.

```mermaid
sequenceDiagram
    autonumber
    participant ClienteHTTP
    participant VentasService
    participant ContratoStock
    participant ContratoCxc
    participant CobranzasService
    participant Tesoreria
    participant BusEventos

    ClienteHTTP->>VentasService: POST /ventas/pedidos (tipo remito)
    VentasService->>VentasService: commit + ventas.remito.creado
    ClienteHTTP->>VentasService: POST .../confirmar-remito
    VentasService->>ContratoStock: egresar por linea
    VentasService->>ContratoCxc: registrar_debe (remito)
    VentasService->>VentasService: commit
    VentasService->>BusEventos: ventas.remito.confirmado
    ClienteHTTP->>VentasService: POST .../facturar
    Note over VentasService,ContratoCxc: CxC ya imputada al remito no duplica debe
    VentasService->>VentasService: commit
    VentasService->>BusEventos: ventas.factura.creada
    ClienteHTTP->>CobranzasService: POST /cobranzas/recibos
    CobranzasService->>ContratoCxc: registrar_haber (recibo)
    alt transferencia
        CobranzasService->>Tesoreria: ContratoBancos.acreditar
    else efectivo o tarjeta
        CobranzasService->>Tesoreria: ContratoCaja.registrar_ingreso
    end
    CobranzasService->>CobranzasService: commit
    CobranzasService->>BusEventos: cobranzas.recibo.creado
```

Espejo de compras: confirmar remito/factura de compra ingresa stock y, si es `factura_compra`, registra debe en CxP (`compras.{tipo}.confirmado`).
