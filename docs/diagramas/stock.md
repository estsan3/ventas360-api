# stock — ajuste y toma de inventario

Fuente: `app/modulos/stock/` · Flujo principal: `POST /api/v1/stock/ajustes`. También: `POST /api/v1/stock/tomas`.
Actualizado: 2026-08-27.

Ajuste relativo (positivo o negativo) sobre saldo de artículo × depósito. Egresos/ingresos de comprobantes van por contrato (`egresar` / `ingresar`) sin commit propio. La toma deja el saldo en las cantidades contadas y sincroniza el stock plano del catálogo.

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

## Cerrar toma de inventario

```mermaid
sequenceDiagram
    participant Cliente
    participant Router as stock.router
    participant Service as StockService
    participant Productos as ContratoProductos
    participant Stock as StockLocal

    Cliente->>Router: POST /stock/tomas deposito, conteos
    Router->>Service: cerrar_toma
    loop cada articulo contado
        Service->>Productos: obtener_producto
        Service->>Stock: obtener_saldo
        Service->>Stock: establecer_cantidad referencia toma_inventario
        Service->>Stock: saldo_total_articulo
        Service->>Productos: establecer_stock total
    end
    Service->>Service: commit
    Service-->>Router: CerrarTomaResponse ajustados y deltas
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
```

Sin commit. Lo hace el service llamador.

## Otros endpoints

| Método | Ruta | operation_id |
|--------|------|----------------|
| GET/POST/PUT/PATCH | `/stock/depositos` | CRUD depósitos |
| GET | `/stock/articulos/{id}/saldos` | `listar_saldos_articulo` |
| GET | `/stock/depositos/{id}/inventario` | `listar_inventario_deposito` (migra stock plano legacy) |
| POST | `/stock/ajustes` | `ajustar_stock` |
| POST | `/stock/tomas` | `cerrar_toma_inventario` |
