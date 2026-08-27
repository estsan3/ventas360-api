# reporteria — KPIs

Fuente: `app/modulos/reporteria/` · Flujo principal: `GET /api/v1/reporteria/kpis`.
Actualizado: 2026-08-27.

Solo lectura: agrega métricas vía contratos. No persiste ni publica eventos. Un comercio nuevo recibe ceros reales (sin números de demo).

```mermaid
sequenceDiagram
    participant Cliente
    participant Router as reporteria.router
    participant Service as ReporteriaService
    participant Clientes as ContratoClientes
    participant Productos as ContratoProductos
    participant Ventas as ContratoVentas
    participant Param as ContratoParametros
    participant Cxc as CxcDAO

    Cliente->>Router: GET /reporteria/kpis
    Router->>Service: obtener_kpis
    Service->>Clientes: contar_activos
    Service->>Productos: contar_activos y bajo_stock
    Service->>Ventas: metricas_dia, metricas_mes, pendientes
    Service->>Ventas: top_articulos, serie_semana, listar_recientes
    Service->>Param: obtener_negocio
    Service->>Cxc: saldos_agrupados
    Service->>Clientes: nombres_por_ids
    Service->>Service: ticket, saldo_cobrar, vencidos
    Service-->>Router: KpisResponse
    Router-->>Cliente: 200
```

Incluye: ventas día/mes, ticket promedio, pendientes, moneda, top artículos, serie de la semana, últimos comprobantes, reposición, CxC a cobrar/vencido.

Hoy `saldos_agrupados` se lee del DAO de cxc (el contrato público no expone ese agregado).

No hay `contrato.py` ni DAO propio: el módulo es un compositor de contratos.
