# compras — confirmar compra

Fuente: `app/modulos/compras/` · Flujo principal: `POST /api/v1/compras/{id}/confirmar`.
Actualizado: 2026-08-26.

Ingreso de stock al depósito. Si el tipo es `factura_compra`, imputa debe en CxP. Misma TX + evento `compras.{tipo}.confirmado`.

```mermaid
sequenceDiagram
    participant Cliente
    participant Router as compras.router
    participant Service as ComprasService
    participant BO as ComprasBO
    participant DAO as ComprasDAO
    participant Stock as ContratoStock
    participant Cxp as ContratoCxp
    participant Bus as bus_eventos

    Cliente->>Router: POST /compras/{id}/confirmar
    Router->>Service: confirmar
    Service->>DAO: buscar_por_id
    Service->>BO: validar_confirmacion
    loop cada linea
        Service->>Stock: ingresar articulo, deposito, cantidad
    end
    alt tipo factura_compra
        Service->>Cxp: registrar_debe proveedor, total, ref factura_compra
    end
    Service->>Service: commit
    Service-)Bus: compras.{tipo}.confirmado
    Service-->>Router: CompraResponse estado confirmado
    Router-->>Cliente: 200
```

## Crear y facturar remito

- `POST /compras`: valida proveedor, depósito, líneas (costo de lista o `precio_unitario`), IVA de parámetros, estado `borrador`.
- `POST /compras/{id}/facturar`: remito confirmado → `factura_compra` + `registrar_debe` CxP + evento `compras.factura_compra.creada`.

## Otros endpoints

| Método | Ruta | operation_id |
|--------|------|----------------|
| GET | `/compras` | `listar_compras` |
| GET | `/compras/{id}` | `obtener_compra` |
| POST | `/compras` | `crear_compra` |
| POST | `/compras/{id}/facturar` | `facturar_remito_compra` |

No hay `contrato.py` de compras.
