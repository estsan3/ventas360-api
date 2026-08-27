# cobranzas — crear recibo

Fuente: `app/modulos/cobranzas/` · Flujo principal: `POST /api/v1/cobranzas/recibos`.
Actualizado: 2026-08-27.

Valida imputaciones contra comprobantes cobrables (remito/factura), registra haber en CxC e impacta tesorería según medio (efectivo/tarjeta → caja; transferencia → banco; cheque → cartera + caja).

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
    Service->>BO: validar_medio, validar_cheque, validar_recibo
    Service->>Clientes: existe_cliente
    loop cada imputacion
        Service->>Ventas: obtener_comprobante_cobrable
    end
    Service->>DAO: guardar Recibo + imputaciones
    Service->>Cxc: registrar_haber referencia recibo
    alt medio transferencia
        Service->>Bancos: acreditar
    else medio cheque
        Service->>Bancos: recibir_cheque origen recibo
        Service->>Caja: registrar_ingreso medio cheque
    else efectivo o tarjeta
        Service->>Caja: registrar_ingreso
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
