# stock — ajuste

Fuente: `app/modulos/stock/` · Flujo principal: `POST /api/v1/stock/ajustes`.
Actualizado: 2026-08-26.

Ajuste relativo (positivo o negativo) sobre saldo de artículo × depósito. Egresos/ingresos de comprobantes van por contrato (`egresar` / `ingresar`) sin commit propio.

```mermaid
sequenceDiagram
    participant Cliente
    participant Router as stock.router
    participant Service as StockService
    participant Productos as ContratoProductos
    participant DAO as StockDAO
    participant BO as StockBO

    Cliente->>Router: POST /stock/ajustes articulo, deposito, cantidad
    Router->>Service: ajustar
    Service->>Productos: obtener_producto
    Service->>DAO: buscar_deposito
    Service->>DAO: buscar_saldo
    Service->>BO: validar_ajuste
    Service->>DAO: guardar_saldo
    Service->>DAO: guardar_movimiento tipo ajuste
    Service->>Service: commit
    Service-->>Router: SaldoResponse
    Router-->>Cliente: 200
```

## Contrato (llamado por ventas/compras/productos)

```mermaid
sequenceDiagram
    participant Orquestador as Ventas o Compras
    participant Stock as StockLocal
    participant DAO as StockDAO
    participant BO as StockBO

    Orquestador->>Stock: egresar o ingresar
    Stock->>DAO: buscar_deposito activo
    Stock->>DAO: buscar_saldo
    Stock->>BO: validar_egreso o validar_ingreso
    Stock->>DAO: movimiento + saldo
    Stock-->>Orquestador: cantidad resultante
    Note over Stock,Orquestador: Sin commit. Lo hace el service llamador.
```

## Otros endpoints

| Método | Ruta | operation_id |
|--------|------|----------------|
| GET/POST/PUT/PATCH | `/stock/depositos` | CRUD depósitos |
| GET | `/stock/articulos/{id}/saldos` | `listar_saldos_articulo` |
| GET | `/stock/depositos/{id}/inventario` | `listar_inventario_deposito` (migra stock plano legacy) |
