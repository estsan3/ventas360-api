"""BO del módulo compras."""

from app.core.excepciones import ReglaDeNegocioViolada

TIPOS = {"remito_compra", "factura_compra"}
ESTADOS = {"borrador", "confirmado", "facturado", "cancelado"}


class ComprasBO:
    def validar_tipo(self, tipo: str) -> None:
        if tipo not in TIPOS:
            raise ReglaDeNegocioViolada(f"Tipo de compra inválido: {tipo}")

    def validar_creacion(self, cantidad_lineas: int) -> None:
        if cantidad_lineas < 1:
            raise ReglaDeNegocioViolada("La compra debe tener al menos una línea")

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
        if estado != "borrador":
            raise ReglaDeNegocioViolada("Solo se confirman compras en borrador")
        if tipo not in TIPOS:
            raise ReglaDeNegocioViolada("Tipo de compra inválido")
        if not deposito_id:
            raise ReglaDeNegocioViolada("La compra requiere deposito_id para ingresar stock")

    def validar_conversion_a_factura(self, tipo: str, estado: str) -> None:
        if tipo != "remito_compra":
            raise ReglaDeNegocioViolada("Solo se factura un remito de compra")
        if estado != "confirmado":
            raise ReglaDeNegocioViolada(
                "El remito de compra debe estar confirmado para facturarlo"
            )
