# bancos — acreditar, cartera de cheques y depositar

Fuente: `app/modulos/bancos/` · Flujos: `ContratoBancos` (cobranzas/caja/pagos) y `POST /api/v1/bancos/valores/{id}/depositar`.
Actualizado: 2026-08-29.

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

## Cartera de cheques (contrato)

```mermaid
sequenceDiagram
    participant Orquestador as Cobranzas o Caja
    participant Bancos as BancosLocal
    participant BO as BancosBO
    participant DAO as BancosDAO

    alt recibir de tercero
        Orquestador->>Bancos: recibir_cheque
        Bancos->>BO: validar_cheque
        Bancos->>DAO: ValorBancario cheque_tercero en_cartera
        Bancos-->>Orquestador: valor_id
    else entregar de cartera
        Orquestador->>Bancos: entregar_cheque valor_id
        Bancos->>BO: validar_entrega estado en_cartera
        Bancos->>DAO: estado entregado
    else emitir propio
        Orquestador->>Bancos: emitir_cheque_propio
        Bancos->>DAO: ValorBancario cheque_propio entregado
        Bancos-->>Orquestador: valor_id
    end
```

Sin commit: lo hace el service orquestador.

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
| GET/POST | `/bancos/valores` | listar (`estado`, `tipo`, `q`) / crear valor en cartera |
| POST | `/bancos/valores/{id}/depositar` | `depositar_valor_bancario` |
| POST | `/bancos/valores/{id}/entregar` | `entregar_valor_bancario` |

`ContratoBancos`: `acreditar`, `debitar`, `recibir_cheque`, `entregar_cheque`, `emitir_cheque_propio`. Usado por **cobranzas**, **caja** y **pagos**.
