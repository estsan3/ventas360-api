# tenants — alta de comercio (plataforma)

Prefijo: `/api/v1/tenants` (público, plataforma y comercio).
Fuentes: `app/modulos/tenants/{router,service,bo,dao,contrato,dependencias,host}.py`.

## POST /tenants (`operation_id`: `crear_tenant`) — solo superadmin en `admin.*`

```mermaid
sequenceDiagram
    autonumber
    participant ClienteHTTP
    participant TenantsRouter
    participant TenantsService
    participant TenantsBO
    participant TenantDAO
    participant ContratoAuth
    participant DB

    ClienteHTTP->>TenantsRouter: POST /tenants + Host admin.*
    TenantsRouter->>TenantsRouter: exigir_host_plataforma + requerir_rol superadmin
    TenantsRouter->>TenantsService: crear(datos)
    TenantsService->>TenantsBO: validar_nombre + validar_slug
    TenantsService->>TenantDAO: buscar_por_slug(slug)
    TenantDAO-->>TenantsService: None (único)
    TenantsService->>TenantDAO: guardar(Tenant) flush
    TenantsService->>ContratoAuth: crear_administrador_inicial(...)
    ContratoAuth-->>TenantsService: admin (flush, sin commit)
    TenantsService->>TenantsService: usando_tenant + asegurar_permisos_default
    TenantsService->>TenantDAO: guardar_permiso(PermisoRol) flush
    TenantsService->>DB: commit
    TenantsService-->>TenantsRouter: TenantCreadoResponse
    TenantsRouter-->>ClienteHTTP: 201
```

## GET /tenants/contexto (`operation_id`: `contexto_tenant_host`) — público

`hostname_desde_request` → `TenantsBO.clasificar_host` → si slug de comercio: `TenantDAO.buscar_por_slug`.

Contrato expuesto: `ContratoTenants`. Usa `ContratoAuth`.
