# tenants — crear comercio

Fuente: `app/modulos/tenants/` · Flujo principal: `POST /api/v1/tenants` (host `admin.*`, rol `superadmin`).
Actualizado: 2026-08-29.

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
| GET | `/tenants` | superadmin | `listar_tenants` |
| GET/PATCH | `/tenants/{id}` | superadmin | obtener / actualizar |
| PATCH | `/tenants/{id}/usuarios/{uid}/password` | superadmin | `cambiar_password_usuario_tenant` |
| GET/PUT | `/tenants/permisos` | comercio + módulo configuracion | matriz de permisos |

## Contrato público

`ContratoTenants`: `contexto_desde_host`, `modulos_habilitados`, `obtener_por_id`, `obtener_por_slug`, `existe_tenant`. Usado por **auth** (login/perfil) e **ia** (webhook n8n via `TenantsService.obtener_por_slug`).
