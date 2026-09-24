# tenants — crear comercio

Fuente: `app/modulos/tenants/` · Flujo principal: `POST /api/v1/tenants` (host `admin.*`, rol `superadmin`).
Actualizado: 2026-09-24.

Alta de comercio + primer administrador + matriz de permisos default, **una transacción**. Los permisos se escriben con `usando_tenant(tenant.id)`.

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
    Service->>DAO: permisos default vendedor/encargado
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
    Service->>Service: clasificar_host plataforma vs slug
    alt host admin (plataforma)
        Service-->>Router: tipo plataforma
    else sin slug (localhost u origen no clasificado)
        Service-->>Router: tipo sin_slug
    else slug de comercio
        Service->>DAO: buscar_por_slug
        DAO-->>Service: Tenant o None
        Service-->>Router: tipo comercio + TenantPublico
    end
    Router-->>Cliente: ContextoHostResponse
```

Hostname: `X-Forwarded-Host` / `X-Original-Host`, luego Origin, Referer y Host (`hostname_desde_request`). Puede devolver `plataforma`, `comercio` o `sin_slug`.

## Otros endpoints

| Método | Ruta | Quién | operation_id |
|--------|------|-------|----------------|
| GET | `/tenants/contexto` | público | `contexto_tenant_host` |
| GET | `/tenants` | superadmin | `listar_tenants` |
| POST | `/tenants` | superadmin | `crear_tenant` |
| GET | `/tenants/{id}` | superadmin | `obtener_tenant` (ficha + usuarios) |
| PATCH | `/tenants/{id}` | superadmin | `actualizar_tenant` (nombre/activo; slug inmutable) |
| PATCH | `/tenants/{id}/usuarios/{uid}/password` | superadmin | `cambiar_password_usuario_tenant` |
| GET | `/tenants/permisos` | comercio + módulo configuracion | `obtener_matriz_permisos` |
| PUT | `/tenants/permisos` | comercio + módulo configuracion | `actualizar_matriz_permisos` |

## Contrato público

`ContratoTenants`: `obtener_por_id`, `obtener_por_slug`, `existe_tenant`, `contexto_desde_host`, `modulos_habilitados`.

Usado por **auth** (login/perfil). El webhook n8n de **ia** llama `TenantsService.obtener_por_slug` en el mismo proceso (sin contrato).
