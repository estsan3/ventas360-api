# proveedores — importar lista Excel

Prefijo: `/api/v1/proveedores`. Módulo HTTP: `compras`.
Fuentes: `app/modulos/proveedores/{router,service,bo,dao,excel,contrato}.py`.

## POST /proveedores/{id}/listas/importar (`operation_id`: `importar_lista_proveedor`)

```mermaid
sequenceDiagram
    autonumber
    participant ClienteHTTP
    participant ProveedoresRouter
    participant ProveedoresService
    participant ProveedorBO
    participant ExcelParser
    participant ContratoProductos
    participant ProveedorDAO
    participant DB

    ClienteHTTP->>ProveedoresRouter: POST .../listas/importar (xlsx)
    ProveedoresRouter->>ProveedoresRouter: validar extension xlsx o xlsm
    ProveedoresRouter->>ProveedoresService: importar_lista(...)
    ProveedoresService->>ProveedorDAO: buscar_por_id
    ProveedoresService->>ProveedorBO: validar_mapeo + validar_politica
    ProveedoresService->>ExcelParser: parsear_lista_excel (sin DB)
    loop cada fila
        ProveedoresService->>ProveedorBO: resolver_precio_venta
        ProveedoresService->>ContratoProductos: obtener_por_sku
        alt no dry_run
            ProveedoresService->>ContratoProductos: upsert_desde_lista
            Note over ContratoProductos: flush, sin commit
        end
    end
    alt no dry_run
        ProveedoresService->>ProveedorDAO: guardar metadata importacion
        ProveedoresService->>DB: commit
    end
    ProveedoresService-->>ProveedoresRouter: ImportarListaResponse
    ProveedoresRouter-->>ClienteHTTP: 200
```

Usa `ContratoProductos`. Expone `ContratoProveedores` (usado por compras).
