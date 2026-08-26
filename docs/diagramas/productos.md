# productos — alta

Fuente: `app/modulos/productos/` · Flujo principal: `POST /api/v1/productos`.
Actualizado: 2026-08-26.

SKU único. Si `stock > 0`, sincroniza el saldo del depósito default vía contrato (misma TX).

```mermaid
sequenceDiagram
    participant Cliente
    participant Router as productos.router
    participant Service as ProductosService
    participant BO as ProductoBO
    participant DAO as ProductoDAO
    participant Stock as ContratoStock

    Cliente->>Router: POST /productos sku, precios, stock
    Router->>Service: crear(datos)
    Service->>DAO: buscar_por_sku
    Service->>BO: validar_alta, validar_stock, validar_precios
    Service->>DAO: guardar Producto
    alt stock mayor a 0
        Service->>Stock: deposito_default_id
        Stock-->>Service: deposito_id
        Service->>Stock: establecer_cantidad articulo, deposito, stock
    end
    Service->>Service: commit
    Service->>Stock: saldo_total_articulo
    Service-->>Router: ProductoResponse
    Router-->>Cliente: 201
```

## Otros endpoints

| Método | Ruta | operation_id |
|--------|------|----------------|
| GET | `/productos` | `listar_productos` (stock via contrato) |
| GET | `/productos/{id}` | `obtener_producto` |
| PUT | `/productos/{id}` | `actualizar_producto` |

## Contrato público

`ContratoProductos`: `obtener_producto`, `obtener_por_sku`, `listar_activos`, `contar_activos`, `upsert_desde_lista`. Usado por **ventas**, **compras**, **precios**, **stock**, **proveedores**, **reporteria**.
