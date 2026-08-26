# precios — upsert de precio en lista

Prefijo: `/api/v1/precios`. Módulo HTTP: `articulos`.
Fuentes: `app/modulos/precios/{router,service,bo,dao,contrato}.py`.

## PUT /precios/articulos (`operation_id`: `upsert_precio_articulo`)

```mermaid
sequenceDiagram
    autonumber
    participant ClienteHTTP
    participant PreciosRouter
    participant PreciosService
    participant PreciosBO
    participant PreciosDAO
    participant ContratoProductos
    participant DB

    ClienteHTTP->>PreciosRouter: PUT /precios/articulos
    PreciosRouter->>PreciosRouter: exigir_usuario_del_comercio + requerir_modulo articulos
    PreciosRouter->>PreciosService: upsert_precio(datos)
    PreciosService->>PreciosBO: validar_precio
    PreciosService->>PreciosDAO: buscar_lista(lista_id)
    PreciosService->>ContratoProductos: obtener_producto(articulo_id)
    PreciosService->>PreciosDAO: buscar_precio(lista_id, articulo_id)
    PreciosService->>PreciosDAO: guardar_precio(PrecioArticulo) flush
    PreciosService->>DB: commit
    PreciosService-->>PreciosRouter: PrecioArticuloResponse
    PreciosRouter-->>ClienteHTTP: 200
```

## GET /precios/resolver

Lista default → override de artículo (`origen: lista`) o `producto.precio` (`origen: catalogo`).

Usa `ContratoProductos`. Expone `ContratoPrecios` (usado por ventas al armar líneas).
