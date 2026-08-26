# stock — ajuste de inventario

Prefijo: `/api/v1/stock`. Módulo HTTP: `stock`.
Fuentes: `app/modulos/stock/{router,service,bo,dao,contrato}.py`.

## POST /stock/ajustes (`operation_id`: `ajustar_stock`)

```mermaid
sequenceDiagram
    autonumber
    participant ClienteHTTP
    participant StockRouter
    participant StockService
    participant ContratoProductos
    participant StockDAO
    participant StockBO
    participant DB

    ClienteHTTP->>StockRouter: POST /stock/ajustes
    StockRouter->>StockRouter: exigir_usuario_del_comercio + requerir_modulo stock
    StockRouter->>StockService: ajustar(datos)
    StockService->>ContratoProductos: obtener_producto(articulo_id)
    StockService->>StockDAO: buscar_deposito(deposito_id)
    StockService->>StockDAO: buscar_saldo(articulo, deposito)
    StockService->>StockBO: validar_ajuste(delta, actual)
    StockService->>StockDAO: guardar_saldo(SaldoStock) flush
    StockService->>StockDAO: guardar_movimiento(tipo ajuste) flush
    StockService->>DB: commit
    StockService-->>StockRouter: SaldoResponse
    StockRouter-->>ClienteHTTP: 200
```

## Contrato (sin commit propio)

`ContratoStock.egresar` / `ingresar` / `establecer_cantidad` — llamados por ventas, compras y productos; el commit lo hace el service orquestador.

Usa `ContratoProductos`. Expone `ContratoStock`.
