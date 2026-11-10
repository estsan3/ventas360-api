# Flujo transversal — request autenticado

Fuente: `app/core/dependencias.py`, `app/modulos/tenants/dependencias.py`, `app/modulos/ia/dependencias.py`, `app/core/eventos.py`.
Actualizado: 2026-11-10.

Casi todos los endpoints de comercio exigen cookie/Bearer JWT **y** que el Host sea el subdominio del tenant del usuario. El `tenant_id` se fija en contexto (`usando_tenant`) para filtrar filas sin ForeignKey entre módulos.

Dependencias típicas de un endpoint de comercio: `obtener_usuario_actual` (JWT) → `exigir_usuario_del_comercio` (Host + match de tenant) → `requerir_modulo(rol)`.

## Request de un comercio

```mermaid
sequenceDiagram
    participant Cliente
    participant FastAPI
    participant JWT as core.seguridad
    participant TenantsDep as tenants.dependencias
    participant TenantsSvc as TenantsService
    participant TenantDAO
    participant Router
    participant Service
    participant DAO

    Cliente->>FastAPI: HTTP + cookie/Bearer + Host slug.localhost
    FastAPI->>JWT: obtener_usuario_actual
    JWT->>JWT: decodificar_token
    JWT-->>FastAPI: UsuarioActual id, rol, tenant_id
    FastAPI->>TenantsDep: exigir_usuario_del_comercio
    TenantsDep->>TenantsSvc: contexto_desde_host(Host)
    TenantsSvc->>TenantDAO: buscar_por_slug
    TenantDAO-->>TenantsSvc: Tenant activo
    TenantsSvc-->>TenantsDep: tipo comercio + tenant_id
    TenantsDep->>TenantsDep: JWT.tenant_id == Host.tenant_id
    TenantsDep->>TenantsDep: usando_tenant
    FastAPI->>TenantsDep: requerir_modulo
    TenantsDep->>TenantsSvc: modulos_habilitados(tenant_id, rol)
    TenantsSvc-->>FastAPI: lista de módulos
    FastAPI->>Router: DTO Request
    Router->>Service: caso de uso
    Service->>DAO: persistir + flush
    Service->>Service: commit
    Service-->>Router: DTO Response
    Router-->>Cliente: JSON
```

## Capas dentro de un módulo

```mermaid
sequenceDiagram
    participant Router
    participant Service
    participant BO
    participant ContratoOtro as Contrato de otro modulo
    participant DAO
    participant Bus as bus_eventos

    Router->>Service: crear / confirmar / ...
    Service->>BO: validar reglas
    BO-->>Service: ok o excepcion de negocio
    Service->>ContratoOtro: IDs debiles (existe / registrar)
    ContratoOtro-->>Service: resultado (sin commit)
    Service->>DAO: guardar + flush
    Service->>Service: commit
    Service-)Bus: EventoDominio modulo.entidad.accion
    Service-->>Router: Response
```

## Excepciones al JWT de comercio

No todos los endpoints pasan por `exigir_usuario_del_comercio` + `requerir_modulo`:

| Caso | Auth |
|------|------|
| `POST /auth/login`, `POST /auth/logout` | sin JWT (logout solo borra cookie) |
| `GET /auth/me` | JWT (`obtener_usuario_actual`) + Host; no exige módulo |
| `GET /tenants/contexto` | público (Host) |
| `GET/PUT /preferencias` | JWT de comercio **sin** `requerir_modulo` |
| CRUD `/tenants` (salvo contexto y permisos) | host `admin.*` + rol `superadmin` |
| `GET /ai/webhook/resumen-dia` | `X-Ventas360-Webhook-Secret` + `X-Tenant-Slug` (sin JWT). Ver [ia.md](ia.md) |

## Convenciones

- Errores: `RecursoNoEncontrado`, `ReglaDeNegocioViolada`, `NoAutenticado`, `NoAutorizado` → `{"error": {"codigo", "mensaje"}}`.
- Contratos **no hacen commit**; el service orquestador cierra la transacción.
- El bus es en memoria; un fallo en un manejador no revierte el commit.
