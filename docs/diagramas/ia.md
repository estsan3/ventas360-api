# ia — mostrador, acciones del día y resumen

Fuente: `app/modulos/ia/` · Flujo principal: `POST /api/v1/ai/mostrador/interpretar`.
Actualizado: 2026-08-29.

No persiste ni publica eventos. Interpreta texto de mostrador (Haiku o mock), matchea cliente y artículos, y arma sugerencias del día a partir de KPIs. El webhook de n8n lee el mismo resumen **sin JWT**: secreto de header + slug de tenant.

Prefijo HTTP: `/api/v1/ai` (inglés, el resto de la API usa nombres en español). Requiere `VENTAS360_AI_HABILITADA` para el mostrador.

## Interpretar mostrador

Permiso: módulo `mostrador`. No crea el comprobante: la UI arma el POST a ventas con el DTO devuelto.

```mermaid
sequenceDiagram
    participant Cliente
    participant Router as ia.router
    participant Service as IaService
    participant LLM as adaptador texto Haiku o mock
    participant Prod as ContratoProductos
    participant Cli as ContratoClientes

    Cliente->>Router: POST /ai/mostrador/interpretar texto
    Router->>Service: interpretar_mostrador
    alt IA deshabilitada
        Service-->>Router: 422 La IA esta deshabilitada
    else Anthropic configurado
        Service->>LLM: PROMPT_MOSTRADOR + texto
        LLM-->>Service: JSON cliente, tipo, lineas
    else mock local
        Service->>Service: mostrador_desde_texto_mock
    end
    Service->>Prod: listar_activos
    Service->>Cli: buscar_por_texto
    Service->>Service: matchear_lineas_mostrador SKU o nombre
    Service-->>Router: InterpretarMostradorResponse
    Router-->>Cliente: 200
```

## Acciones y resumen del día

Permiso: módulo `inicio`. `acciones_del_dia` no llama al LLM. `resumen_dia` opcionalmente pide narrativa a Haiku.

Hoy `IaService` lee `ReporteriaService` y `ComprasDAO` en el mismo proceso (no hay `contrato.py` de IA ni de compras para este agregado). El diseño de capas pide contratos; el diagrama refleja el código actual.

```mermaid
sequenceDiagram
    participant Cliente
    participant Router as ia.router
    participant Service as IaService
    participant Rep as ReporteriaService
    participant Compras as ComprasDAO
    participant BO as IaBO
    participant LLM as adaptador texto Haiku o mock

    Cliente->>Router: GET /ai/acciones
    Router->>Service: acciones_del_dia
    Service->>Rep: obtener_kpis
    Service->>Compras: listar remito_compra borrador
    Service->>BO: construir_acciones
    Service-->>Router: AccionesDiaResponse

    Cliente->>Router: GET /ai/resumen-dia
    Router->>Service: resumen_dia
    Service->>Rep: obtener_kpis
    Service->>Compras: listar remito_compra borrador
    Service->>BO: construir_acciones
    opt narrativa true
        alt Anthropic configurado
            Service->>LLM: PROMPT_RESUMEN + metricas
        else mock
            Service->>BO: narrativa_mock
        end
    end
    Service-->>Router: ResumenDiaResponse
```

## Webhook n8n (sin JWT)

```mermaid
sequenceDiagram
    participant n8n
    participant Router as ia.router
    participant Dep as ia.dependencias
    participant Tenants as TenantsService
    participant Service as IaService

    n8n->>Router: GET /ai/webhook/resumen-dia
    Note over n8n,Dep: Headers X-Ventas360-Webhook-Secret y X-Tenant-Slug
    Router->>Dep: verificar_webhook_n8n
    Dep->>Dep: comparar secreto VENTAS360_N8N_WEBHOOK_SECRET
    Router->>Dep: fijar_tenant_por_slug
    Dep->>Tenants: obtener_por_slug
    Dep->>Dep: usando_tenant
    Router->>Service: resumen_dia
    Service-->>Router: ResumenDiaResponse
    Router-->>n8n: 200
```

## Endpoints

| Método | Ruta | operation_id | Auth |
|--------|------|----------------|------|
| POST | `/ai/mostrador/interpretar` | `interpretar_mostrador` | JWT + módulo `mostrador` |
| GET | `/ai/acciones` | `acciones_del_dia` | JWT + módulo `inicio` |
| GET | `/ai/resumen-dia` | `resumen_dia` | JWT + módulo `inicio` |
| GET | `/ai/webhook/resumen-dia` | `webhook_resumen_dia_n8n` | secreto + slug (sin JWT) |

No hay `contrato.py`. Consumidores internos: **productos**, **clientes**, **reporteria**, **compras** (DAO), **tenants**.
