# ventas — confirmar remito

Fuente: `app/modulos/ventas/` · Flujo principal: `POST /api/v1/ventas/pedidos/{id}/confirmar-remito`.
Actualizado: 2026-08-26.

Egreso de stock + debe en CxC en la **misma transacción**. Luego publica `ventas.remito.confirmado` (hooks locales no-op; otros módulos pueden suscribirse).

```mermaid
sequenceDiagram
    participant Cliente
    participant Router as ventas.router
    participant Service as VentasService
    participant BO as VentasBO
    participant DAO as VentasDAO
    participant Stock as ContratoStock
    participant Cxc as ContratoCxc
    participant Bus as bus_eventos

    Cliente->>Router: POST /ventas/pedidos/{id}/confirmar-remito
    Router->>Service: confirmar_remito
    Service->>DAO: buscar_por_id
    Service->>BO: validar_confirmacion_remito
    loop cada linea
        Service->>Stock: egresar articulo, deposito, cantidad
    end
    Service->>Cxc: registrar_debe cliente, total, ref remito
    Service->>Service: commit
    Service-)Bus: ventas.remito.confirmado
    Service-->>Router: PedidoResponse estado confirmado
    Router-->>Cliente: 200
```

## Crear comprobante (contexto)

`POST /ventas/pedidos`: valida cliente, arma líneas con `ContratoProductos` + `ContratoPrecios`, IVA y número de `ContratoParametros`, commit, evento `ventas.{tipo}.creado`.

Facturar remito (`POST .../facturar`): si el remito **ya** tiene movimiento CxC, no vuelve a imputar. Evento `ventas.factura.creada`.

## Otros endpoints

| Método | Ruta | operation_id |
|--------|------|----------------|
| GET | `/ventas/pedidos` | `listar_pedidos` |
| GET | `/ventas/pedidos/{id}` | `obtener_pedido` |
| POST | `/ventas/pedidos` | `crear_pedido` |
| PATCH | `/ventas/pedidos/{id}/estado` | `cambiar_estado_pedido` |
| POST | `/ventas/pedidos/{id}/facturar` | `facturar_remito` |

## Contrato público

`ContratoVentas`: métricas, pendientes, top artículos, `obtener_comprobante_cobrable`. Usado por **reporteria** y **cobranzas**.
