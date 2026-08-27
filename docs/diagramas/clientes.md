# clientes — alta

Fuente: `app/modulos/clientes/` · Flujo principal: `POST /api/v1/clientes`.
Actualizado: 2026-08-27.

Valida email único, datos comerciales, vendedor (auth) y zona (IDs débiles).

```mermaid
sequenceDiagram
    participant ClienteHTTP
    participant Router as clientes.router
    participant Service as ClientesService
    participant DAO as ClienteDAO
    participant BO as ClienteBO
    participant Auth as ContratoAuth
    participant Zonas as ContratoZonas

    ClienteHTTP->>Router: POST /clientes
    Router->>Service: crear(datos)
    Service->>DAO: buscar_por_email
    Service->>BO: validar_alta y validar_datos_comerciales
    Service->>Auth: existe_usuario(vendedor_id)
    Auth-->>Service: bool
    Service->>Zonas: existe_zona(zona_id)
    Zonas-->>Service: bool
    Service->>DAO: guardar Cliente
    Service->>Service: commit
    Service-->>Router: ClienteResponse
    Router-->>ClienteHTTP: 201
```

## Otros endpoints

| Método | Ruta | operation_id |
|--------|------|----------------|
| GET | `/clientes` | `listar_clientes` (paginado) |
| GET | `/clientes/{id}` | `obtener_cliente` |
| PUT | `/clientes/{id}` | `actualizar_cliente` |
| PATCH | `/clientes/{id}` | `desactivar_cliente` |

## Contrato público

`ContratoClientes`: `existe_cliente`, `contar_activos`, `nombres_por_ids`. Usado por **ventas**, **cxc**, **cobranzas**, **reporteria**.
