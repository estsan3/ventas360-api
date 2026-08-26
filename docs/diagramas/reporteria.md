# reporteria — KPIs del dashboard

Prefijo: `/api/v1/reporteria`. Módulo HTTP: `inicio`.
Fuentes: `app/modulos/reporteria/{router,service,schemas}.py`.

## GET /reporteria/kpis (`operation_id`: `obtener_kpis`)

```mermaid
sequenceDiagram
    autonumber
    participant ClienteHTTP
    participant ReporteriaRouter
    participant ReporteriaService
    participant ContratoClientes
    participant ContratoProductos
    participant ContratoVentas
    participant ContratoParametros

    ClienteHTTP->>ReporteriaRouter: GET /reporteria/kpis
    ReporteriaRouter->>ReporteriaRouter: exigir_usuario_del_comercio + requerir_modulo inicio
    ReporteriaRouter->>ReporteriaService: obtener_kpis
    ReporteriaService->>ContratoClientes: contar_activos
    ReporteriaService->>ContratoProductos: contar_activos
    ReporteriaService->>ContratoVentas: metricas_dia
    ReporteriaService->>ContratoVentas: metricas_mes
    ReporteriaService->>ContratoVentas: pendientes
    ReporteriaService->>ContratoVentas: top_articulos(5)
    ReporteriaService->>ContratoParametros: obtener_negocio
    ReporteriaService->>ReporteriaService: ticket_promedio = monto_mes / cantidad_mes
    ReporteriaService-->>ReporteriaRouter: KpisResponse
    ReporteriaRouter-->>ClienteHTTP: 200
```

Solo lectura: no persiste ni publica eventos. Agrega métricas vía contratos (sin importar DAO ajenos).
