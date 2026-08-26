# productos — alta de producto + stock inicial

Prefijo: `/api/v1/productos`. Módulo HTTP: `articulos`.
Fuentes: `app/modulos/productos/{router,service,bo,dao,contrato}.py`.

## POST /productos (`operation_id`: `crear_producto`)

```mermaid
sequenceDiagram
    autonumber
    participant ClienteHTTP
    participant ProductosRouter
    participant ProductosService
    participant ProductoBO
    participant ProductoDAO
    participant ContratoStock
    participant DB

    ClienteHTTP->>ProductosRouter: POST /productos
    ProductosRouter->>ProductosRouter: exigir_usuario_del_comercio + requerir_modulo articulos
    ProductosRouter->>ProductosService: crear(datos)
    ProductosService->>ProductoDAO: buscar_por_sku
    ProductosService->>ProductoBO: validar_alta + validar_stock + validar_precios
    ProductosService->>ProductoDAO: guardar(Producto) flush
    alt stock inicial mayor a 0
        ProductosService->>ContratoStock: deposito_default_id
        ProductosService->>ContratoStock: establecer_cantidad(articulo, deposito, stock)
        Note over ContratoStock: flush, sin commit
    end
    ProductosService->>DB: commit
    ProductosService->>ContratoStock: saldo_total_articulo
    ProductosService-->>ProductosRouter: ProductoResponse
    ProductosRouter-->>ClienteHTTP: 201
```

Usa `ContratoStock`. Expone `ContratoProductos` (`obtener_producto`, `obtener_por_sku`, `upsert_desde_lista`, `contar_activos`).
