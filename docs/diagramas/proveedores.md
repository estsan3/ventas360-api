# proveedores — importar lista Excel

Fuente: `app/modulos/proveedores/` · Flujo principal: `POST /api/v1/proveedores/{id}/listas/importar`.
Actualizado: 2026-08-26.

Parsea `.xlsx`, resuelve precio de venta según política y hace upsert de artículos vía `ContratoProductos` (misma TX). `dry_run=true` no persiste.

```mermaid
sequenceDiagram
    participant Cliente
    participant Router as proveedores.router
    participant Service as ProveedoresService
    participant Excel as parsear_lista_excel
    participant BO as ProveedorBO
    participant Productos as ContratoProductos
    participant DAO as ProveedorDAO

    Cliente->>Router: POST /proveedores/{id}/listas/importar archivo xlsx
    Router->>Service: importar_lista
    Service->>DAO: buscar_por_id
    Service->>BO: validar_mapeo y validar_politica
    Service->>Excel: parsear bytes
    Excel-->>Service: filas
    loop cada fila
        Service->>BO: resolver_precio_venta
        Service->>Productos: obtener_por_sku
        alt no dry_run
            Service->>Productos: upsert_desde_lista
        end
    end
    alt no dry_run
        Service->>DAO: metadata ultima_importacion
        Service->>Service: commit
    end
    Service-->>Router: ImportarListaResponse
    Router-->>Cliente: 200
```

## Otros endpoints

| Método | Ruta | operation_id |
|--------|------|----------------|
| GET | `/proveedores` | `listar_proveedores` |
| GET | `/proveedores/{id}` | `obtener_proveedor` |
| POST | `/proveedores` | `crear_proveedor` |
| PUT | `/proveedores/{id}` | `actualizar_proveedor` |
| PATCH | `/proveedores/{id}` | `desactivar_proveedor` |

## Contrato público

`ContratoProveedores.existe_proveedor`. Usado por **compras**.
