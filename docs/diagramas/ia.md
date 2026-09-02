# ia — interpretar mostrador y resumen del día

Fuente: `app/modulos/ia/` · Prefijo HTTP: `/api/v1/ai`.
Actualizado: 2026-09-01.

El módulo no persiste ni publica eventos. Interpreta texto del mostrador, arma acciones del día y un resumen narrativo. El webhook de n8n replica el resumen **sin JWT** (secreto + slug de tenant).

No hay `contrato.py`. Hoy `IaService` consume `ReporteriaService` y `ComprasDAO` en el mismo proceso (sin contrato). Clientes y productos sí van por contrato.

## Interpretar mostrador (flujo principal)

`POST /ai/mostrador/interpretar` · JWT + módulo `mostrador`. Requiere `VENTAS360_AI_HABILITADA`.

```mermaid
sequenceDiagram
    participant Cliente
    participant Router as ia.router
    participant Service as IaService
    participant LLM as adaptador texto
    participant Clientes as ContratoClientes
    participant Productos as ContratoProductos

    Cliente->>Router: POST /ai/mostrador/interpretar texto
    Router->>Service: interpretar_mostrador
    alt anthropic_api_key y modo no mock
        Service->>LLM: llamar_haiku_texto PROMPT_MOSTRADOR
        LLM-->>Service: JSON extraido
    else
        Service->>Service: mostrador_desde_texto_mock
    end
    Service->>Productos: listar_activos
    alt hay cliente_texto
        Service->>Clientes: buscar_por_texto
    end
    Service->>Service: matchear_lineas_mostrador SKU o nombre
    Service-->>Router: InterpretarMostradorResponse
    Router-->>Cliente: 200
```

No crea el comprobante: el front arma el POST a **ventas** con `cliente_id` y `producto_id` ya resueltos.

## Acciones y resumen del día

```mermaid
sequenceDiagram
    participant Cliente
    participant Router as ia.router
    participant Service as IaService
    participant Reporteria as ReporteriaService
    participant Compras as ComprasDAO
    participant BO as ia.bo
    participant LLM as adaptador texto

    Cliente->>Router: GET /ai/acciones o /ai/resumen-dia
    Router->>Service: acciones_del_dia o resumen_dia
    Service->>Reporteria: obtener_kpis
    Service->>Compras: listar remito_compra borrador
    Service->>BO: construir_acciones
    alt resumen con narrativa y anthropic
        Service->>LLM: llamar_haiku_texto PROMPT_RESUMEN
    else narrativa mock
        Service->>BO: narrativa_mock
    end
    Service-->>Router: AccionesDiaResponse o ResumenDiaResponse
    Router-->>Cliente: 200
```

## Webhook n8n (sin JWT)

`GET /ai/webhook/resumen-dia` · headers `X-Ventas360-Webhook-Secret` y `X-Tenant-Slug`.

```mermaid
sequenceDiagram
    participant N8n
    participant Dep as ia.dependencias
    participant Tenants as TenantsService
    participant Router as ia.router
    participant Service as IaService

    N8n->>Dep: secreto + X-Tenant-Slug
    Dep->>Dep: verificar_webhook_n8n
    Dep->>Tenants: obtener_por_slug
    Tenants-->>Dep: tenant activo
    Dep->>Dep: usando_tenant
    Dep->>Router: webhook_resumen_dia_n8n
    Router->>Service: resumen_dia
    Service-->>N8n: ResumenDiaResponse
```

Si falta `VENTAS360_N8N_WEBHOOK_SECRET` o el secreto no coincide → `NoAutenticado`.

## Endpoints

| Método | Ruta | operation_id | Auth |
|--------|------|----------------|------|
| POST | `/ai/mostrador/interpretar` | `interpretar_mostrador` | JWT + módulo `mostrador` |
| GET | `/ai/acciones` | `acciones_del_dia` | JWT + módulo `inicio` |
| GET | `/ai/resumen-dia` | `resumen_dia` | JWT + módulo `inicio` |
| GET | `/ai/webhook/resumen-dia` | `webhook_resumen_dia_n8n` | secreto + slug |

Query `narrativa=true` (default) en los dos resúmenes.

## Contratos que consume

- `ContratoClientes.buscar_por_texto`
- `ContratoProductos.listar_activos`

Puerto de texto: `adaptadores/texto.py` (Haiku). Visión de remitos de compra está en [compras.md](compras.md), no acá.
