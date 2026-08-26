# clientes — alta de cliente

Prefijo: `/api/v1/clientes`. Módulo HTTP: `clientes`.
Fuentes: `app/modulos/clientes/{router,service,bo,dao,contrato}.py`.

## POST /clientes (`operation_id`: `crear_cliente`)

```mermaid
sequenceDiagram
    autonumber
    participant ClienteHTTP
    participant ClientesRouter
    participant ClientesService
    participant ClienteBO
    participant ClienteDAO
    participant ContratoAuth
    participant ContratoZonas
    participant DB

    ClienteHTTP->>ClientesRouter: POST /clientes
    ClientesRouter->>ClientesRouter: exigir_usuario_del_comercio + requerir_modulo clientes
    ClientesRouter->>ClientesService: crear(datos)
    ClientesService->>ClienteDAO: buscar_por_email
    ClientesService->>ClienteBO: validar_alta + validar_datos_comerciales
    ClientesService->>ContratoAuth: existe_usuario(vendedor_id)
    ClientesService->>ClienteBO: validar_vendedor
    ClientesService->>ContratoZonas: existe_zona(zona_id)
    ClientesService->>ClienteDAO: guardar(Cliente) flush
    ClientesService->>DB: commit
    ClientesService-->>ClientesRouter: ClienteResponse
    ClientesRouter-->>ClienteHTTP: 201
```

Usa `ContratoAuth` y `ContratoZonas`. Expone `ContratoClientes` (`existe_cliente`, `contar_activos`).
