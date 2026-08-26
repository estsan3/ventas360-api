# ventas — confirmar remito (stock + CxC)

Prefijo: `/api/v1/ventas`. Módulos HTTP: `mostrador` o `ventas`.
Fuentes: `app/modulos/ventas/{router,service,bo,dao,contrato,eventos}.py`.

## POST /ventas/pedidos/{id}/confirmar-remito (`operation_id`: `confirmar_remito`)

```mermaid
sequenceDiagram
    autonumber
    participant ClienteHTTP
    participant VentasRouter
    participant VentasService
    participant VentasBO
    participant VentasDAO
    participant ContratoStock
    participant ContratoCxc
    participant BusEventos
    participant DB

    ClienteHTTP->>VentasRouter: POST .../confirmar-remito
    VentasRouter->>VentasService: confirmar_remito(remito_id)
    VentasService->>VentasDAO: buscar_por_id
    VentasService->>VentasBO: validar_confirmacion_remito
    loop cada linea
        VentasService->>ContratoStock: egresar(articulo, deposito, cantidad)
        Note over ContratoStock: referencia remito:id flush
    end
    VentasService->>VentasService: remito.estado = confirmado
    VentasService->>ContratoCxc: registrar_debe(cliente, total, remito)
    Note over ContratoCxc: idempotente por referencia flush
    VentasService->>DB: commit
    VentasService->>BusEventos: ventas.remito.confirmado
    VentasService-->>VentasRouter: PedidoResponse
    VentasRouter-->>ClienteHTTP: 200
```

## Otros flujos

| operation_id | Resumen |
|--------------|---------|
| `crear_pedido` | Valida cliente/producto, resuelve precio, IVA, talonario, commit, evento `ventas.{tipo}.creado` |
| `facturar_remito` | Remito confirmado → factura; CxC solo si el remito no tenía debe; evento `ventas.factura.creada` |
| `cambiar_estado_pedido` | Transición BO; remito→confirmado redirige a `confirmar_remito` |

Usa: `ContratoClientes`, `ContratoProductos`, `ContratoPrecios`, `ContratoStock`, `ContratoParametros`, `ContratoCxc`.
Expone: `ContratoVentas`.
Publica: `ventas.{tipo}.creado`, `ventas.{tipo}.estado_cambiado`, `ventas.remito.confirmado`, `ventas.factura.creada`.
