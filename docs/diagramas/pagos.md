# pagos — pago a proveedor

Fuente: `app/modulos/pagos/` · Flujo principal: `POST /api/v1/pagos`.
Actualizado: 2026-08-28.

Espejo de cobranzas. Baja deuda (CxP haber) e impacta tesorería: efectivo → caja, transferencia → banco, cheque de cartera → `entregar_cheque`, cheque propio → `emitir_cheque_propio`.

La UI vive en Tesorería (`/tesoreria/pagos`). Este módulo API queda suelto.

```mermaid
sequenceDiagram
    participant Cliente
    participant Router as pagos.router
    participant Service as PagosService
    participant BO as PagosBO
    participant Prov as ContratoProveedores
    participant DAO as PagosDAO
    participant Cxp as ContratoCxp
    participant Caja as ContratoCaja
    participant Bancos as ContratoBancos
    participant Bus as bus_eventos

    Cliente->>Router: POST /pagos proveedor, medios
    Router->>Service: crear
    Service->>BO: validar_medios
    Service->>Prov: existe_proveedor
    Service->>DAO: guardar Pago + lineas
    loop cada medio
        alt efectivo
            Service->>Caja: registrar_egreso
        else transferencia
            Service->>Bancos: debitar
        else cheque de cartera
            Service->>Bancos: entregar_cheque
        else cheque propio
            Service->>Bancos: emitir_cheque_propio
        end
    end
    Service->>Cxp: registrar_haber pago_proveedor
    Service->>Service: commit
    Service-)Bus: pagos.pago.creado
    Service-->>Router: PagoResponse
```

## Endpoints

| Método | Ruta | operation_id |
|--------|------|----------------|
| GET | `/pagos` | `listar_pagos_proveedor` |
| GET | `/pagos/{id}` | `obtener_pago_proveedor` |
| POST | `/pagos` | `crear_pago_proveedor` |

Permiso: módulo `compras`. No hay `contrato.py`.
