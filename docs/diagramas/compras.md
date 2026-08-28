# compras — confirmar compra

Fuente: `app/modulos/compras/` · Flujo principal: `POST /api/v1/compras/{id}/confirmar`.
Actualizado: 2026-08-28.

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

## Parsear remito desde foto

`POST /compras/remitos/parsear` (multipart: JPEG/PNG/WebP). **Solo lectura**: extrae líneas con visión (puerto `PuertoParserRemitoVision`) y las matchea al catálogo. No crea la compra; el operador confirma con `POST /compras`.

Adaptador: `mock`, `anthropic` o `auto` (`VENTAS360_REMITO_PARSE_MODO`). En `auto`, Haiku si hay API key; si no, mock.

```mermaid
sequenceDiagram
    participant Cliente
    participant Router as compras.router
    participant Service as ComprasService
    participant Proveedores as ContratoProveedores
    participant Parser as PuertoParserRemitoVision
    participant Productos as ContratoProductos

    Cliente->>Router: POST /compras/remitos/parsear archivo
    Router->>Service: parsear_remito_foto
    Service->>Service: validar imagen y tamaño
    opt proveedor_id informado
        Service->>Proveedores: existe_proveedor
    end
    Service->>Parser: parsear bytes, media_type
    Parser-->>Service: RemitoExtraido
    Service->>Productos: listar_activos
    loop lineas con codigo de barras
        Service->>Productos: obtener_por_codigo_barras
    end
    Service->>Service: matchear SKU, barras o nombre
    Service-->>Router: ParsearRemitoResponse
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
| POST | `/compras/remitos/parsear` | `parsear_remito_foto` |
| POST | `/compras/{id}/confirmar` | `confirmar_compra` |
| POST | `/compras/{id}/facturar` | `facturar_remito_compra` |

No hay `contrato.py` de compras. El parser de visión vive en `puerto.py` + `adaptadores/`.
