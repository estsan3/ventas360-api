# cobranzas — crear recibo

Fuente: `app/modulos/cobranzas/` · Flujo principal: `POST /api/v1/cobranzas/recibos`.
Actualizado: 2026-08-28.

Valida imputaciones contra comprobantes cobrables (remito/factura), registra **un** haber en CxC por el monto del recibo e impacta tesorería por cada línea de medio. Las imputaciones pueden ser menores al monto (a cuenta) o vacías (anticipo); no pueden superarlo.

Medios: un solo `medio` o lista `medios` (efectivo, tarjeta, transferencia, cheque; máximo 3 cheques). Si hay más de una línea, el recibo persiste `medio=mixto`. Cada línea de tesorería usa referencia `recibo_id` o `recibo_id:índice` para idempotencia.

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

La UI suele imputar deudas de más antigua a más reciente; el API aplica las imputaciones que llegan en el request (FIFO es decisión del cliente HTTP).

## Otros endpoints

| Método | Ruta | operation_id |
|--------|------|----------------|
| GET | `/cobranzas/recibos` | `listar_recibos` |
| GET | `/cobranzas/recibos/{id}` | `obtener_recibo` |

No hay `contrato.py` de cobranzas: el módulo orquesta a otros.
