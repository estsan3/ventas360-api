"""BO del módulo compras."""

from app.core.excepciones import ReglaDeNegocioViolada

TIPOS = {"pedido_compra", "remito_compra", "factura_compra"}
TIPOS_CON_STOCK = {"remito_compra", "factura_compra"}
ESTADOS_PEDIDO = {
    "borrador",
    "emitido",
    "parcial",
    "recibido",
    "cerrado",
    "cancelado",
}


class ComprasBO:
    def validar_tipo(self, tipo: str) -> None:
        if tipo not in TIPOS:
            raise ReglaDeNegocioViolada(f"Tipo de compra inválido: {tipo}")

    def validar_creacion(self, cantidad_lineas: int) -> None:
        if cantidad_lineas < 1:
            raise ReglaDeNegocioViolada("La compra debe tener al menos una línea")

    def validar_linea(self, producto_id: str | None, codigo_proveedor: str | None) -> None:
        if not (producto_id or "").strip() and not (codigo_proveedor or "").strip():
            raise ReglaDeNegocioViolada(
                "Cada línea requiere artículo del catálogo o código de proveedor"
            )

    def calcular_importes(
        self, totales_lineas: float, iva_porcentaje: float
    ) -> tuple[float, float, float]:
        neto = round(totales_lineas, 2)
        iva = round(neto * (iva_porcentaje / 100.0), 2)
        total = round(neto + iva, 2)
        return neto, iva, total

    def validar_confirmacion(
        self, tipo: str, estado: str, deposito_id: str | None
    ) -> None:
        if tipo == "pedido_compra":
            raise ReglaDeNegocioViolada(
                "El pedido de compra no ingresa stock. Emitilo y recibí un remito."
            )
        if estado != "borrador":
            raise ReglaDeNegocioViolada("Solo se confirman compras en borrador")
        if tipo not in TIPOS_CON_STOCK:
            raise ReglaDeNegocioViolada("Tipo de compra inválido")
        if not deposito_id:
            raise ReglaDeNegocioViolada("La compra requiere deposito_id para ingresar stock")

    def validar_lineas_con_articulo(self, sin_articulo: int) -> None:
        if sin_articulo > 0:
            raise ReglaDeNegocioViolada(
                "Hay líneas sin artículo del catálogo. Dales de alta con SKU propio "
                "antes de confirmar el remito."
            )

    def validar_emitir_pedido(self, tipo: str, estado: str) -> None:
        if tipo != "pedido_compra":
            raise ReglaDeNegocioViolada("Solo se emite un pedido de compra")
        if estado != "borrador":
            raise ReglaDeNegocioViolada("Solo se emite un pedido en borrador")

    def estado_pedido_segun_recepcion(self, pedida: int, recibida: int) -> str:
        if pedida <= 0 or recibida <= 0:
            return "emitido"
        if recibida < pedida:
            return "parcial"
        return "recibido"

    def validar_conversion_a_factura(self, tipo: str, estado: str) -> None:
        if tipo != "remito_compra":
            raise ReglaDeNegocioViolada("Solo se factura un remito de compra")
        if estado != "confirmado":
            raise ReglaDeNegocioViolada(
                "El remito de compra debe estar confirmado para facturarlo"
            )
