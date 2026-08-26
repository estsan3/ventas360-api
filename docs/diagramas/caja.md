# caja — ingreso

Fuente: `app/modulos/caja/` · Flujos: contrato `registrar_ingreso` (cobranzas) y `POST /api/v1/caja/movimientos` (manual).
Actualizado: 2026-08-26.

El contrato es idempotente por referencia y **no commitea**. El alta HTTP es movimiento `manual`.

```mermaid
sequenceDiagram
    participant Cobranzas as CobranzasService
    participant Caja as CajaLocal
    participant BO as CajaBO
    participant DAO as CajaDAO

    Cobranzas->>Caja: registrar_ingreso monto, medio, ref recibo
    Caja->>BO: validar_movimiento
    Caja->>DAO: existe_referencia
    alt ya existe
        Caja-->>Cobranzas: no-op
    else nuevo
        Caja->>DAO: guardar MovimientoCaja tipo ingreso
        Caja-->>Cobranzas: ok
    end
```

## Movimiento manual HTTP

```mermaid
sequenceDiagram
    participant Cliente
    participant Router as caja.router
    participant Service as CajaService
    participant BO as CajaBO
    participant DAO as CajaDAO

    Cliente->>Router: POST /caja/movimientos tipo, medio, monto
    Router->>Service: crear_movimiento
    Service->>BO: validar_movimiento
    Service->>DAO: guardar referencia_tipo manual
    Service->>Service: commit
    Service-->>Router: MovimientoCajaResponse
    Router-->>Cliente: 201
```

## Otros endpoints

| Método | Ruta | operation_id |
|--------|------|----------------|
| GET | `/caja/movimientos` | `listar_movimientos_caja` |
| GET | `/caja/saldo` | `saldo_caja` |

`ContratoCaja`: `registrar_ingreso`, `registrar_egreso`. Usado por **cobranzas**.
