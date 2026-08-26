# bancos — acreditar (cobranzas) y depositar valor

Prefijo: `/api/v1/bancos`. Módulo HTTP: `compras`.
Fuentes: `app/modulos/bancos/{router,service,bo,dao,contrato}.py`.

## Contrato: acreditar (recibo transferencia)

```mermaid
sequenceDiagram
    autonumber
    participant CobranzasService
    participant ContratoBancos
    participant BancosBO
    participant BancosDAO
    participant DB

    CobranzasService->>ContratoBancos: acreditar(monto, recibo)
    ContratoBancos->>BancosBO: validar_movimiento
    ContratoBancos->>BancosDAO: existe_referencia_mov
    ContratoBancos->>BancosDAO: buscar_cuenta_default
    ContratoBancos->>BancosDAO: guardar_movimiento(credito) flush
    Note over CobranzasService,DB: commit en CobranzasService
    ContratoBancos-->>CobranzasService: ok
```

## POST /bancos/valores/{id}/depositar (`operation_id`: `depositar_valor_bancario`)

```mermaid
sequenceDiagram
    autonumber
    participant ClienteHTTP
    participant BancosRouter
    participant BancosService
    participant BancosBO
    participant BancosDAO
    participant DB

    ClienteHTTP->>BancosRouter: POST /bancos/valores/{id}/depositar
    BancosRouter->>BancosService: depositar_valor(valor_id, datos)
    BancosService->>BancosDAO: buscar_valor
    BancosService->>BancosBO: validar_deposito (estado en_cartera)
    BancosService->>BancosDAO: buscar_cuenta o buscar_cuenta_default
    BancosService->>BancosService: valor.estado = depositado
    BancosService->>BancosDAO: guardar_movimiento(credito) flush
    BancosService->>BancosDAO: guardar_valor flush
    BancosService->>DB: commit
    BancosService-->>BancosRouter: ValorBancarioResponse
    BancosRouter-->>ClienteHTTP: 200
```

Expone `ContratoBancos` (`acreditar`, `debitar`). Sin eventos.
