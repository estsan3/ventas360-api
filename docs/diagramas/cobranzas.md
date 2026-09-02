# cobranzas — crear recibo

Fuente: `app/modulos/cobranzas/` · Flujo principal: `POST /api/v1/cobranzas/recibos`.
Actualizado: 2026-08-29.

Valida medios (uno o mixtos) e imputaciones contra comprobantes cobrables (remito/factura). Un haber en CxC por recibo. Tesorería por **línea**: efectivo/tarjeta → caja; transferencia → banco; cheque → cartera + caja.

Las imputaciones pueden sumar **menos** que el monto (anticipo / a cuenta). Si no hay imputaciones, el haber igual baja el saldo del cliente.

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

    Cliente->>Router: POST /cobranzas/recibos medios e imputaciones
    Router->>Service: crear
    Service->>BO: normalizar_medios y validar_medios
    Service->>BO: validar_recibo suma imputaciones menor o igual al monto
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
    Service-->>Router: ReciboResponse medio o mixto
    Router-->>Cliente: 201
```

## Otros endpoints

| Método | Ruta | operation_id |
|--------|------|----------------|
| GET | `/cobranzas/recibos` | `listar_recibos` |
| GET | `/cobranzas/recibos/{id}` | `obtener_recibo` |

No hay `contrato.py` de cobranzas: el módulo orquesta a otros.
