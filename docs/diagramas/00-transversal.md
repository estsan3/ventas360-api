# Flujo transversal — request autenticado

Fuente: `app/core/dependencias.py`, `app/modulos/tenants/dependencias.py`, `app/modulos/ia/dependencias.py`, `app/core/eventos.py`.
Actualizado: 2026-11-12.

Casi todos los endpoints de comercio exigen cookie/Bearer JWT **y** que el Host sea el subdominio del tenant del usuario (`exigir_usuario_del_comercio`). El `tenant_id` se fija en contexto (`usando_tenant`) para filtrar filas sin ForeignKey entre módulos. El JWT se reconstruye solo desde claims (`obtener_usuario_actual`), sin ir a la base.

## Request de un comercio

```mermaid
sequenceDiagram
    participant Cliente
    participant DepJWT as core.dependencias
    participant JWT as core.seguridad
    participant DepTenant as tenants.dependencias
    participant TenantsSvc as TenantsService
    participant TenantDAO
    participant Router
    participant Service
    participant DAO

    Cliente->>DepJWT: HTTP + cookie/Bearer + Host slug.localhost
    DepJWT->>JWT: decodificar_token
    JWT-->>DepJWT: UsuarioActual id, rol, tenant_id
    DepJWT->>DepTenant: exigir_usuario_del_comercio
    DepTenant->>TenantsSvc: contexto_desde_host(Host)
    TenantsSvc->>TenantDAO: buscar_por_slug
    TenantDAO-->>TenantsSvc: Tenant activo
    TenantsSvc-->>DepTenant: tipo comercio + tenant_id
    DepTenant->>DepTenant: JWT.tenant_id == Host.tenant_id
    DepTenant->>DepTenant: usando_tenant
    Note over DepTenant: requerir_modulo(rol) si el endpoint lo declara
    DepTenant->>TenantsSvc: modulos_habilitados(tenant_id, rol)
    TenantsSvc-->>DepTenant: lista de módulos
    DepTenant->>Router: DTO Request
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

## Excepción: webhook n8n

`GET /api/v1/ai/webhook/resumen-dia` no usa JWT. Autentica con `X-Ventas360-Webhook-Secret` y fija el tenant con `X-Tenant-Slug` (`ia.dependencias`). Ver [ia.md](ia.md).

Plataforma (`admin.*` + rol `superadmin`): `exigir_host_plataforma` + `requerir_rol("superadmin")`. Ver [tenants.md](tenants.md).

## Convenciones

- Errores: `RecursoNoEncontrado`, `ReglaDeNegocioViolada`, `NoAutenticado`, `NoAutorizado` → `{"error": {"codigo", "mensaje"}}`.
- Contratos **no hacen commit**; el service orquestador cierra la transacción.
- El bus es en memoria; un fallo en un manejador no revierte el commit.
- Suscripciones registradas hoy: solo `ventas.remito.confirmado` y `ventas.factura.creada` (hooks locales no-op).
