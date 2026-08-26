# Flujo transversal — autenticación, tenant y permisos

Fuentes: `app/core/dependencias.py`, `app/core/seguridad.py`, `app/modulos/tenants/dependencias.py`, `app/modulos/tenants/host.py`.

Casi todos los endpoints de comercio declaran:

```python
dependencies=[
    Depends(exigir_usuario_del_comercio),
    Depends(requerir_modulo("...")),
]
```

## Request autenticado de un comercio

```mermaid
sequenceDiagram
    autonumber
    participant ClienteHTTP
    participant Router
    participant CoreAuth
    participant DependenciasTenants
    participant TenantsService
    participant TenantDAO
    participant ServiceModulo

    ClienteHTTP->>Router: Request + Host + Cookie o Bearer
    Router->>CoreAuth: obtener_usuario_actual
    CoreAuth->>CoreAuth: decodificar JWT (sin DB)
    CoreAuth-->>Router: UsuarioActual
    Router->>DependenciasTenants: exigir_usuario_del_comercio
    DependenciasTenants->>DependenciasTenants: hostname_desde_request
    DependenciasTenants->>TenantsService: contexto_desde_host(host)
    TenantsService->>TenantDAO: buscar_por_slug(slug)
    TenantDAO-->>TenantsService: Tenant activo
    TenantsService-->>DependenciasTenants: tipo comercio + tenant.id
    DependenciasTenants->>DependenciasTenants: usando_tenant(tenant.id)
    Note over DependenciasTenants: JWT.tenant_id debe coincidir con el Host
    DependenciasTenants-->>Router: tenant_id
    Router->>DependenciasTenants: requerir_modulo(...)
    DependenciasTenants->>TenantsService: modulos_habilitados(tenant_id, rol)
    TenantsService-->>DependenciasTenants: lista de módulos
    DependenciasTenants-->>Router: UsuarioActual
    Router->>ServiceModulo: caso de uso
    ServiceModulo-->>Router: DTO
    Router-->>ClienteHTTP: JSON 200
```

## Errores unificados

`ErrorDeNegocio` (`NoAutenticado`, `NoAutorizado`, `RecursoNoEncontrado`, `ReglaDeNegocioViolada`) → handler en `app/main.py` → `{"error": {"codigo", "mensaje"}}`.
