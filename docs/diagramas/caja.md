# caja — ingreso y cierre

Fuente: `app/modulos/caja/` · Flujos: contrato `registrar_ingreso` (cobranzas), `POST /api/v1/caja/movimientos` y `POST /api/v1/caja/cerrar`.
Actualizado: 2026-08-27.

El contrato es idempotente por referencia y **no commitea**. El alta HTTP exige caja abierta ese día. El cierre compara esperado vs contado en efectivo, cheques y tarjetas.

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
        Caja->>DAO: buscar_abierta (sesion_id opcional)
        Caja->>DAO: guardar MovimientoCaja tipo ingreso
        Caja-->>Cobranzas: ok
    end
```

## Movimiento manual HTTP (incluye cheques)

```mermaid
sequenceDiagram
    participant Cliente
    participant Router as caja.router
    participant Service as CajaService
    participant BO as CajaBO
    participant DAO as CajaDAO
    participant Bancos as ContratoBancos

    Cliente->>Router: POST /caja/movimientos tipo, medio, monto
    Router->>Service: crear_movimiento
    Service->>BO: validar_movimiento
    Service->>DAO: buscar_abierta
    Service->>BO: validar_caja_abierta
    alt medio cheque ingreso
        Service->>Bancos: recibir_cheque en_cartera
    else medio cheque egreso con cheque_id
        Service->>Bancos: entregar_cheque
    else medio cheque egreso propio
        Service->>Bancos: emitir_cheque_propio
    end
    Service->>DAO: guardar referencia_tipo manual o cheque
    Service->>Service: commit
    Service-->>Router: MovimientoCajaResponse
    Router-->>Cliente: 201
```

## Cerrar caja (efectivo / cheque / tarjeta)

```mermaid
sequenceDiagram
    participant Cliente
    participant Router as caja.router
    participant Service as CajaService
    participant BO as CajaBO
    participant DAO as CajaDAO

    Cliente->>Router: POST /caja/cerrar efectivo, cheques, tarjetas
    Router->>Service: cerrar
    Service->>BO: validar_contado por medio
    Service->>DAO: buscar_abierta
    Service->>DAO: totales_fecha efectivo, cheque, tarjeta
    Service->>BO: calcular_diferencia esperado vs contado
    Service->>Service: sesion cerrada + tres diferencias
    Service->>Service: commit
    Service-->>Router: SaldoCajaResponse
    Router-->>Cliente: 200
```

## Otros endpoints

| Método | Ruta | operation_id |
|--------|------|----------------|
| GET | `/caja/movimientos` | `listar_movimientos_caja` |
| GET | `/caja/saldo` | `saldo_caja` (esperado por medio) |
| POST | `/caja/abrir` | `abrir_caja` (fondo inicial → ingreso efectivo) |
| POST | `/caja/cerrar` | `cerrar_caja` |
| POST | `/caja/movimientos` | `crear_movimiento_caja` |

`ContratoCaja`: `registrar_ingreso`, `registrar_egreso`. Usado por **cobranzas**.
