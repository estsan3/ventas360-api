# cxc — debe vía contrato (desde ventas)

Prefijo HTTP: `/api/v1/cxc` (consultas + ajuste manual).
Fuentes: `app/modulos/cxc/{router,service,bo,dao,contrato}.py`.

La escritura típica **no** entra por HTTP: `VentasService` y `CobranzasService` llaman `ContratoCxc`. El commit queda en el service orquestador.

## Contrato: registrar_debe (confirmación de remito)

```mermaid
sequenceDiagram
    autonumber
    participant VentasService
    participant ContratoCxc
    participant CxcBO
    participant CxcDAO
    participant DB

    VentasService->>ContratoCxc: registrar_debe(cliente, monto, remito)
    ContratoCxc->>CxcBO: validar_movimiento
    ContratoCxc->>CxcDAO: existe_referencia(tipo, id)
    alt ya existe
        CxcDAO-->>ContratoCxc: skip (idempotente)
    else nuevo
        ContratoCxc->>CxcDAO: guardar(MovimientoCxc) flush
    end
    Note over VentasService,DB: commit en VentasService
    ContratoCxc-->>VentasService: ok
```

## POST /cxc/ajustes (`operation_id`: `registrar_ajuste_cxc`)

`CxcService.registrar_ajuste` → `existe_cliente` → `registrar_debe` o `registrar_haber` → **commit propio**.

Usa `ContratoClientes`. Expone `ContratoCxc`. Sin eventos.
