# precios — upsert artículo en lista

Fuente: `app/modulos/precios/` · Flujo principal: `PUT /api/v1/precios/articulos`.
Actualizado: 2026-08-26.

Crea o actualiza el precio de un artículo en una lista. La resolución de venta (lista default → catálogo) la consume **ventas** vía `ContratoPrecios.obtener_precio`.

```mermaid
sequenceDiagram
    participant Cliente
    participant Router as precios.router
    participant Service as PreciosService
    participant BO as PreciosBO
    participant DAO as PreciosDAO
    participant Productos as ContratoProductos

    Cliente->>Router: PUT /precios/articulos lista_id, articulo_id, precio
    Router->>Service: upsert_precio
    Service->>BO: validar_precio
    Service->>DAO: buscar_lista
    Service->>Productos: obtener_producto
    Productos-->>Service: ProductoResumen
    Service->>DAO: buscar_precio
    alt no existe
        Service->>DAO: guardar PrecioArticulo nuevo
    else existe
        Service->>DAO: actualizar precio
    end
    Service->>Service: commit
    Service-->>Router: PrecioArticuloResponse
    Router-->>Cliente: 200
```

## Resolución de precio (contrato / GET `/precios/resolver`)

Lista default con override → si no, `producto.precio` del catálogo. `cliente_id` está reservado (listas por cliente, Fase B).

## Otros endpoints

| Método | Ruta | operation_id |
|--------|------|----------------|
| GET/POST/PUT/PATCH | `/precios/listas` | CRUD listas |
| GET | `/precios/listas/{id}/articulos` | `listar_precios_lista` |
| GET | `/precios/resolver` | `resolver_precio` |

## Contrato público

`ContratoPrecios.obtener_precio(articulo_id, cliente_id)`. Usado por **ventas**.
