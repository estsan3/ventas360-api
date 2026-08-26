# bancos — acreditar y depositar valor

Fuente: `app/modulos/bancos/` · Flujos: `ContratoBancos.acreditar` (cobranzas transferencia) y `POST /api/v1/bancos/valores/{id}/depositar`.
Actualizado: 2026-08-26.

## Acreditar (contrato, misma TX que cobranzas)

```mermaid
sequenceDiagram
    participant Cobranzas as CobranzasService
    participant Bancos as BancosLocal
    participant BO as BancosBO
    participant DAO as BancosDAO

    Cobranzas->>Bancos: acreditar monto, ref recibo
    Bancos->>BO: validar_movimiento
    Bancos->>DAO: existe_referencia_mov
    Bancos->>DAO: buscar_cuenta_default o cuenta_id
    Bancos->>DAO: guardar MovimientoBancario tipo credito
    Bancos-->>Cobranzas: ok
```

## Depositar valor en cartera

```mermaid
sequenceDiagram
    participant Cliente
    participant Router as bancos.router
    participant Service as BancosService
    participant BO as BancosBO
    participant DAO as BancosDAO

    Cliente->>Router: POST /bancos/valores/{id}/depositar
    Router->>Service: depositar_valor
    Service->>DAO: buscar_valor
    Service->>BO: validar_deposito estado en_cartera
    Service->>DAO: cuenta destino o default
    Service->>DAO: movimiento credito + valor depositado
    Service->>Service: commit
    Service-->>Router: ValorBancarioResponse
    Router-->>Cliente: 200
```

## Otros endpoints

| Método | Ruta | operation_id |
|--------|------|----------------|
| GET/POST | `/bancos/cuentas` | listar / crear cuenta |
| GET | `/bancos/movimientos` | `listar_movimientos_bancarios` |
| GET/POST | `/bancos/valores` | listar / crear valor en cartera |

`ContratoBancos`: `acreditar`, `debitar`. Usado por **cobranzas**.
