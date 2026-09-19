# tenants — crear comercio

Fuente: `app/modulos/tenants/` · Flujo principal: `POST /api/v1/tenants` (host `admin.*`, rol `superadmin`).
Actualizado: 2026-09-19.

Alta de comercio + primer administrador + matriz de permisos default, **una transacción**.

```mermaid
sequenceDiagram
    participant Plataforma
    participant Router as tenants.router
    participant Service as TenantsService
    participant BO as TenantsBO
    participant DAO as TenantDAO
    participant Auth as ContratoAuth

    Plataforma->>Router: POST /tenants slug, nombre, administrador
    Router->>Service: crear(datos)
    Service->>BO: validar_nombre y validar_slug
    Service->>DAO: buscar_por_slug
    DAO-->>Service: None
    Service->>DAO: guardar Tenant
    Service->>Auth: crear_administrador_inicial
    Auth-->>Service: AdministradorInicial
    Service->>Service: asegurar_permisos_default (usando_tenant)
    Service->>Service: commit
    Service-->>Router: TenantCreadoResponse
    Router-->>Plataforma: 201
```

## Contexto de Host (público)

```mermaid
sequenceDiagram
    participant Cliente
    participant Router as tenants.router
    participant Service as TenantsService
    participant DAO as TenantDAO

    Cliente->>Router: GET /tenants/contexto + Host
    Router->>Service: contexto_desde_host
    Service->>Service: clasificar_host plataforma, slug o sin_slug
    alt host admin (plataforma)
        Service-->>Router: tipo plataforma
    else sin slug
        Service-->>Router: tipo sin_slug
    else slug de comercio
        Service->>DAO: buscar_por_slug
        DAO-->>Service: Tenant o None
        Service-->>Router: tipo comercio + TenantPublico
    end
    Router-->>Cliente: ContextoHostResponse
```

## Otros endpoints

| Método | Ruta | Quién | operation_id |
|--------|------|-------|----------------|
| GET | `/tenants/contexto` | público (Host) | `contexto_tenant_host` |
| GET | `/tenants` | superadmin | `listar_tenants` |
| POST | `/tenants` | superadmin | `crear_tenant` |
| GET | `/tenants/{tenant_id}` | superadmin | `obtener_tenant` |
| PATCH | `/tenants/{tenant_id}` | superadmin | `actualizar_tenant` |
| PATCH | `/tenants/{tenant_id}/usuarios/{usuario_id}/password` | superadmin | `cambiar_password_usuario_tenant` |
| GET | `/tenants/permisos` | comercio + módulo configuracion | `obtener_matriz_permisos` |
| PUT | `/tenants/permisos` | comercio + módulo configuracion | `actualizar_matriz_permisos` |

## Contrato público

`ContratoTenants`: `obtener_por_id`, `obtener_por_slug`, `existe_tenant`, `contexto_desde_host`, `modulos_habilitados`. Usado por **auth** (login/perfil). El webhook n8n de **ia** llama `TenantsService.obtener_por_slug` (mismo proceso, sin contrato).
