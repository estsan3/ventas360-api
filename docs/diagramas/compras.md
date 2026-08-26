# compras — confirmar compra (stock + CxP)

Prefijo: `/api/v1/compras`.
Fuentes: `app/modulos/compras/{router,service,bo,dao}.py`.

## POST /compras/{id}/confirmar (`operation_id`: `confirmar_compra`)

```mermaid
sequenceDiagram
    autonumber
    participant ClienteHTTP
    participant ComprasRouter
    participant ComprasService
    participant ComprasBO
    participant ComprasDAO
    participant ContratoStock
    participant ContratoCxp
    participant BusEventos
    participant DB

    ClienteHTTP->>ComprasRouter: POST /compras/{id}/confirmar
    ComprasRouter->>ComprasService: confirmar(compra_id)
    ComprasService->>ComprasDAO: buscar_por_id
    ComprasService->>ComprasBO: validar_confirmacion
    loop cada linea
        ComprasService->>ContratoStock: ingresar(articulo, deposito, cantidad)
        Note over ContratoStock: referencia tipo:id flush
    end
    ComprasService->>ComprasService: compra.estado = confirmado
    alt tipo factura_compra
        ComprasService->>ContratoCxp: registrar_debe(proveedor, total)
    end
    ComprasService->>DB: commit
    ComprasService->>BusEventos: compras.{tipo}.confirmado
    ComprasService-->>ComprasRouter: CompraResponse
    ComprasRouter-->>ClienteHTTP: 200
```

## Otros flujos

| operation_id | Resumen |
|--------------|---------|
| `crear_compra` | Valida proveedor, arma líneas, IVA, estado borrador, commit |
| `facturar_remito_compra` | Remito confirmado → factura_compra + debe CxP; evento `compras.factura_compra.creada` |

Usa: `ContratoProveedores`, `ContratoProductos`, `ContratoStock`, `ContratoParametros`, `ContratoCxp`.
No expone contrato.
