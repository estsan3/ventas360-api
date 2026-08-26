# cobranzas — crear recibo (CxC + tesorería)

Prefijo: `/api/v1/cobranzas`.
Fuentes: `app/modulos/cobranzas/{router,service,bo,dao}.py`.

## POST /cobranzas/recibos (`operation_id`: `crear_recibo`)

```mermaid
sequenceDiagram
    autonumber
    participant ClienteHTTP
    participant CobranzasRouter
    participant CobranzasService
    participant CobranzasBO
    participant ContratoClientes
    participant ContratoVentas
    participant CobranzasDAO
    participant ContratoCxc
    participant Tesoreria
    participant BusEventos
    participant DB

    ClienteHTTP->>CobranzasRouter: POST /cobranzas/recibos
    CobranzasRouter->>CobranzasService: crear(datos)
    CobranzasService->>CobranzasBO: validar_medio + validar_recibo
    CobranzasService->>ContratoClientes: existe_cliente
    loop cada imputacion
        CobranzasService->>ContratoVentas: obtener_comprobante_cobrable
    end
    CobranzasService->>CobranzasDAO: guardar(Recibo) flush
    CobranzasService->>ContratoCxc: registrar_haber(recibo)
    alt medio transferencia
        CobranzasService->>Tesoreria: ContratoBancos.acreditar
    else efectivo o tarjeta
        CobranzasService->>Tesoreria: ContratoCaja.registrar_ingreso
    end
    CobranzasService->>DB: commit
    CobranzasService->>BusEventos: cobranzas.recibo.creado
    CobranzasService-->>CobranzasRouter: ReciboResponse
    CobranzasRouter-->>ClienteHTTP: 201
```

Usa: `ContratoClientes`, `ContratoVentas`, `ContratoCxc`, `ContratoCaja`, `ContratoBancos`.
No expone contrato. Publica `cobranzas.recibo.creado`.
