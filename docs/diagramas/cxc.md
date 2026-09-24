# cxc — registrar debe (contrato)

Fuente: `app/modulos/cxc/` · Flujo principal: `ContratoCxc.registrar_debe` (invocado por ventas al confirmar remito / confirmar factura).
Actualizado: 2026-09-24.

El HTTP de CxC es de consulta y ajustes manuales. El debe operativo lo escriben **ventas** y el haber **cobranzas**, sin commit en el contrato (idempotente por `referencia_tipo` + `referencia_id`).

No hay imputación FIFO dentro de CxC: el recibo registra **un** haber por el monto total; las imputaciones a remito/factura viven en **cobranzas**.

```mermaid
sequenceDiagram
    participant Ventas as VentasService
    participant Cxc as CxcLocal
    participant BO as CxcBO
    participant DAO as CxcDAO

    Ventas->>Cxc: registrar_debe cliente, monto, remito, id
    Cxc->>BO: validar_movimiento
    Cxc->>DAO: existe_referencia
    alt ya existe
        Cxc-->>Ventas: no-op idempotente
    else nuevo
        Cxc->>DAO: guardar MovimientoCxc tipo debe
        Cxc-->>Ventas: ok
    end
    Note over Ventas,DAO: Commit lo hace VentasService
```

## Ajuste HTTP (`POST /cxc/ajustes`)

```mermaid
sequenceDiagram
    participant Cliente
    participant Router as cxc.router
    participant Service as CxcService
    participant Clientes as ContratoClientes
    participant Local as CxcLocal

    Cliente->>Router: POST /cxc/ajustes tipo debe o haber
    Router->>Service: registrar_ajuste
    Service->>Clientes: existe_cliente
    Service->>Local: registrar_debe o registrar_haber ref ajuste
    Service->>Service: commit
    Service-->>Router: MovimientoCxcResponse
    Router-->>Cliente: 201
```

Ajustes: módulo `configuracion`. Consultas: módulo `cta_cte`.

## Otros endpoints

| Método | Ruta | operation_id |
|--------|------|----------------|
| GET | `/cxc/saldos` | `listar_saldos_cxc` |
| GET | `/cxc/clientes/{id}/saldo` | `obtener_saldo_cxc` |
| GET | `/cxc/clientes/{id}/estado-cuenta` | `estado_cuenta_cxc` |
| POST | `/cxc/ajustes` | `registrar_ajuste_cxc` |

Saldo = debe − haber (`CxcBO.calcular_saldo`). El listado de saldos incluye `fecha_debe_mas_antigua` (vencidos de reportería).

## Contrato público

`ContratoCxc`: `registrar_debe`, `registrar_haber`, `saldo_cliente`, `existe_referencia`. Usado por **ventas** y **cobranzas**. **reporteria** lee `CxcDAO.saldos_agrupados` en el mismo proceso (el contrato no expone ese agregado).
