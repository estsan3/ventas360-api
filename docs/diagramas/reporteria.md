# reporteria — KPIs

Fuente: `app/modulos/reporteria/` · Flujo principal: `GET /api/v1/reporteria/kpis`.
Actualizado: 2026-08-26.

Solo lectura: agrega métricas vía contratos. No persiste ni publica eventos.

```mermaid
sequenceDiagram
    participant Cliente
    participant Router as reporteria.router
    participant Service as ReporteriaService
    participant Clientes as ContratoClientes
    participant Productos as ContratoProductos
    participant Ventas as ContratoVentas
    participant Param as ContratoParametros

    Cliente->>Router: GET /reporteria/kpis
    Router->>Service: obtener_kpis
    Service->>Clientes: contar_activos
    Service->>Productos: contar_activos
    Service->>Ventas: metricas_dia
    Service->>Ventas: metricas_mes
    Service->>Ventas: pendientes
    Service->>Ventas: top_articulos 5
    Service->>Param: obtener_negocio
    Service->>Service: ticket_promedio monto_mes / cantidad
    Service-->>Router: KpisResponse
    Router-->>Cliente: 200
```

Incluye: ventas día/mes, ticket promedio, pedidos/remitos pendientes, remitos por facturar, moneda, top artículos.

No hay `contrato.py` ni DAO propio: el módulo es un compositor de contratos.
