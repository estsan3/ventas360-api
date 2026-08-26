# parametros — guardar negocio y talonario

Prefijos: `/api/v1/parametros`, `/api/v1/preferencias` (sin prefix de router).
Fuentes: `app/modulos/parametros/{router,service,bo,dao,contrato}.py`.

## PUT /parametros (`operation_id`: `guardar_parametros`)

```mermaid
sequenceDiagram
    autonumber
    participant ClienteHTTP
    participant ParametrosRouter
    participant ParametrosService
    participant ParametrosDAO
    participant TenantCtx
    participant DB

    ClienteHTTP->>ParametrosRouter: PUT /parametros
    ParametrosRouter->>ParametrosRouter: exigir_usuario_del_comercio + requerir_modulo configuracion
    ParametrosRouter->>ParametrosService: guardar_negocio(datos)
    ParametrosService->>TenantCtx: tenant_id_actual
    ParametrosService->>ParametrosDAO: guardar_varios(iva_porcentaje, moneda)
    ParametrosService->>DB: commit
    ParametrosService-->>ParametrosRouter: ParametrosNegocio
    ParametrosRouter-->>ClienteHTTP: 200
```

## Contrato: asignar_numero (usado por ventas)

`ParametrosLocal.asignar_numero(tipo_comprobante)` incrementa `Talonario.proximo_numero` (flush). El commit lo hace `VentasService`.

Sin contratos entrantes. Expone `ContratoParametros` (ventas, compras, reportería).
