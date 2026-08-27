# cxp — registrar debe (contrato)

Fuente: `app/modulos/cxp/` · Flujo principal: `ContratoCxp.registrar_debe` (invocado por compras al confirmar/facturar).
Actualizado: 2026-08-26.

Sin endpoints de escritura HTTP: el debe lo escribe **compras**. El router solo consulta saldos y estado de cuenta. Idempotente por referencia; sin commit en el contrato.

```mermaid
sequenceDiagram
    participant Compras as ComprasService
    participant Cxp as CxpLocal
    participant BO as CxpBO
    participant DAO as CxpDAO

    Compras->>Cxp: registrar_debe proveedor, monto, factura_compra, id
    Cxp->>BO: validar_movimiento
    Cxp->>DAO: existe_referencia
    alt ya existe
        Cxp-->>Compras: no-op idempotente
    else nuevo
        Cxp->>DAO: guardar MovimientoCxp tipo debe
        Cxp-->>Compras: ok
    end
    Note over Compras,DAO: Commit lo hace ComprasService
```

## Consulta HTTP

```mermaid
sequenceDiagram
    participant Cliente
    participant Router as cxp.router
    participant Service as CxpService
    participant DAO as CxpDAO
    participant BO as CxpBO

    Cliente->>Router: GET /cxp/proveedores/{id}/estado-cuenta
    Router->>Service: estado_cuenta
    Service->>DAO: listar_por_proveedor + totales
    Service->>BO: calcular_saldo debe haber
    Service-->>Router: EstadoCuentaProveedorResponse
    Router-->>Cliente: 200
```

## Endpoints

| Método | Ruta | operation_id |
|--------|------|----------------|
| GET | `/cxp/saldos` | `listar_saldos_cxp` |
| GET | `/cxp/proveedores/{id}` | `estado_cuenta_proveedor` |

`ContratoCxp` también expone `registrar_haber` y `saldo_proveedor` (aún sin orquestador HTTP de pagos a proveedores).
