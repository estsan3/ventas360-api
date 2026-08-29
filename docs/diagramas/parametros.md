# parametros — guardar negocio

Fuente: `app/modulos/parametros/` · Flujo principal: `PUT /api/v1/parametros`.
Actualizado: 2026-08-29.

Claves por tenant (`iva_porcentaje`, `moneda`). El contrato `asignar_numero` lo usan **ventas** (talonario, sin commit propio).

```mermaid
sequenceDiagram
    participant Cliente
    participant Router as parametros.router
    participant Service as ParametrosService
    participant DAO as ParametrosDAO

    Cliente->>Router: PUT /parametros iva_porcentaje, moneda
    Router->>Service: guardar_negocio
    Service->>DAO: guardar_varios tenant actual
    Service->>Service: commit
    Service-->>Router: ParametrosNegocio
    Router-->>Cliente: 200
```

## Asignar número de talonario (contrato)

```mermaid
sequenceDiagram
    participant Ventas as VentasService
    participant Param as ParametrosLocal
    participant DAO as ParametrosDAO
    participant BO as ParametrosBO

    Ventas->>Param: asignar_numero tipo remito o factura
    Param->>DAO: buscar_talonario_por_tipo
    Param->>BO: formatear_numero prefijo + proximo
    Param->>DAO: proximo_numero + 1
    Param-->>Ventas: numero
    Note over Ventas,DAO: Sin commit. Lo hace VentasService.
```

## Otros endpoints

| Método | Ruta | operation_id |
|--------|------|----------------|
| GET | `/parametros` | `obtener_parametros` |
| GET/PUT | `/parametros/operativos` | sucursal y condiciones de pago |
| GET/PUT | `/parametros/afip` | identidad fiscal ARCA (emisor) |
| GET/PUT | `/parametros/talonarios` | `listar_talonarios` / `upsert_talonario` |
| GET/PUT | `/preferencias` | notificaciones |
| GET | `/parametria/categorias-producto` | `listar_categorias_producto` |

## Contrato público

`ContratoParametros`: `obtener_negocio`, `obtener_afip`, `asignar_numero`. Usado por **ventas**, **compras**, **reporteria**.
