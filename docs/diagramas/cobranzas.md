# cobranzas — crear recibo

Fuente: `app/modulos/cobranzas/` · Flujo principal: `POST /api/v1/cobranzas/recibos`.
Actualizado: 2026-08-30.

Valida imputaciones contra comprobantes cobrables (remito/factura), registra **un** haber en CxC (referencia `recibo`) e impacta tesorería **por cada línea de medio**.

Medios: un `medio` + `cheque` opcional, o `medios[]` (efectivo, transferencia, tarjeta, cheque). Si hay más de una línea, el recibo queda `mixto`. Hasta 3 cheques. La suma de medios debe igualar el monto.

Imputaciones opcionales: la suma no puede superar el monto. Si suma menos, el resto queda **a cuenta** (anticipo). Si no hay imputaciones, todo el haber es a cuenta.

```mermaid
sequenceDiagram
    participant Cliente
    participant Router as cobranzas.router
    participant Service as CobranzasService
    participant BO as CobranzasBO
    participant Clientes as ContratoClientes
    participant Ventas as ContratoVentas
    participant DAO as CobranzasDAO
    participant Cxc as ContratoCxc
    participant Caja as ContratoCaja
    participant Bancos as ContratoBancos
    participant Bus as bus_eventos

    Cliente->>Router: POST /cobranzas/recibos
    Router->>Service: crear
    Service->>BO: normalizar_medios y validar_medios
    Service->>BO: validar_recibo monto vs imputaciones
    Service->>Clientes: existe_cliente
    loop cada imputacion
        Service->>Ventas: obtener_comprobante_cobrable
    end
    Service->>DAO: guardar Recibo + imputaciones
    Service->>Cxc: registrar_haber referencia recibo
    loop cada linea de medio
        alt transferencia
            Service->>Bancos: acreditar
        else cheque
            Service->>Bancos: recibir_cheque origen recibo
            Service->>Caja: registrar_ingreso medio cheque
        else efectivo o tarjeta
            Service->>Caja: registrar_ingreso
        end
    end
    Service->>Service: commit
    Service-)Bus: cobranzas.recibo.creado
    Service-->>Router: ReciboResponse
    Router-->>Cliente: 201
```

## Otros endpoints

| Método | Ruta | operation_id |
|--------|------|----------------|
| GET | `/cobranzas/recibos` | `listar_recibos` |
| GET | `/cobranzas/recibos/{id}` | `obtener_recibo` |

No hay `contrato.py` de cobranzas: el módulo orquesta a otros.
