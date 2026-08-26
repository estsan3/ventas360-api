# Flujo transversal — request autenticado

Fuente: `app/core/dependencias.py`, `app/modulos/tenants/dependencias.py`, `app/core/eventos.py`.
Actualizado: 2026-08-26.

Casi todos los endpoints de comercio exigen cookie/Bearer JWT **y** que el Host sea el subdominio del tenant del usuario. El `tenant_id` se fija en contexto (`usando_tenant`) para filtrar filas sin ForeignKey entre módulos.

## Request de un comercio

```mermaid
sequenceDiagram
    participant Cliente
    participant FastAPI
    participant JWT as core.seguridad
    participant TenantsSvc as TenantsService
    participant TenantDAO
    participant Router
    participant Service
    participant DAO

    Cliente->>FastAPI: HTTP + cookie/Bearer + Host slug.localhost
    FastAPI->>JWT: decodificar_token
    JWT-->>FastAPI: UsuarioActual id, rol, tenant_id
    FastAPI->>TenantsSvc: contexto_desde_host(Host)
    TenantsSvc->>TenantDAO: buscar_por_slug
    TenantDAO-->>TenantsSvc: Tenant activo
    TenantsSvc-->>FastAPI: tipo comercio + tenant_id
    FastAPI->>FastAPI: exigir JWT.tenant_id == Host.tenant_id
    FastAPI->>TenantsSvc: modulos_habilitados(rol)
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

## Convenciones

- Errores: `RecursoNoEncontrado`, `ReglaDeNegocioViolada`, `NoAutenticado`, `NoAutorizado` → `{"error": {"codigo", "mensaje"}}`.
- Contratos **no hacen commit**; el service orquestador cierra la transacción.
- El bus es en memoria; un fallo en un manejador no revierte el commit.
