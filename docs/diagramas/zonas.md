# zonas — alta de zona

Prefijo: `/api/v1/zonas`. Módulos HTTP: `clientes` o `configuracion`.
Fuentes: `app/modulos/zonas/{router,service,bo,dao,contrato}.py`.

## POST /zonas (`operation_id`: `crear_zona`)

```mermaid
sequenceDiagram
    autonumber
    participant ClienteHTTP
    participant ZonasRouter
    participant ZonasService
    participant ZonaBO
    participant ZonaDAO
    participant DB

    ClienteHTTP->>ZonasRouter: POST /zonas
    ZonasRouter->>ZonasRouter: exigir_usuario_del_comercio + requerir_modulo
    ZonasRouter->>ZonasService: crear(datos)
    ZonasService->>ZonaBO: validar_nombre
    ZonasService->>ZonaDAO: buscar_por_nombre
    ZonaDAO-->>ZonasService: None (único)
    ZonasService->>ZonaDAO: guardar(Zona) flush
    ZonasService->>DB: commit
    ZonasService-->>ZonasRouter: ZonaResponse
    ZonasRouter-->>ClienteHTTP: 201
```

Sin contratos entrantes. Expone `ContratoZonas.existe_zona` (usado por clientes).
