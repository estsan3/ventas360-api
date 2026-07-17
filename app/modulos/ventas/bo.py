"""Capa BO del módulo ventas: reglas puras (sin DB, sin HTTP)."""

from app.core.excepciones import ReglaDeNegocioViolada

TIPOS = {"pedido", "remito", "factura"}

_TRANSICIONES: dict[str, dict[str, set[str]]] = {
    "pedido": {
        "borrador": {"confirmado", "cancelado"},
        "confirmado": {"entregado", "cancelado"},
        "entregado": set(),
        "cancelado": set(),
    },
    "remito": {
        "borrador": {"confirmado", "cancelado"},
        "confirmado": {"facturado", "cancelado"},
        "facturado": set(),
        "cancelado": set(),
    },
    "factura": {
        "borrador": {"confirmado", "cancelado"},
        "confirmado": set(),
        "cancelado": set(),
    },
}


class VentasBO:
    """Reglas de negocio de comprobantes tipados."""

    def validar_tipo(self, tipo: str) -> None:
        if tipo not in TIPOS:
            raise ReglaDeNegocioViolada(f"Tipo de comprobante inválido: {tipo}")

    def validar_creacion(self, cantidad_lineas: int) -> None:
        if cantidad_lineas < 1:
            raise ReglaDeNegocioViolada("El comprobante debe tener al menos una línea")

    def validar_cantidad(self, cantidad: int) -> None:
        if cantidad <= 0:
            raise ReglaDeNegocioViolada("La cantidad debe ser mayor a cero")

    def validar_transicion(self, tipo: str, estado_actual: str, nuevo_estado: str) -> None:
        self.validar_tipo(tipo)
        if nuevo_estado == estado_actual:
            raise ReglaDeNegocioViolada(f"El comprobante ya está en estado {nuevo_estado}")
        permitidos = _TRANSICIONES.get(tipo, {}).get(estado_actual, set())
        if nuevo_estado not in permitidos:
            raise ReglaDeNegocioViolada(
                f"No se puede pasar de {estado_actual} a {nuevo_estado} en {tipo}"
            )

    def validar_confirmacion_remito(self, tipo: str, estado: str, deposito_id: str | None) -> None:
        if tipo != "remito":
            raise ReglaDeNegocioViolada("Solo se pueden confirmar remitos")
        if estado != "borrador":
            raise ReglaDeNegocioViolada("Solo un remito en borrador se puede confirmar")
        if not deposito_id:
            raise ReglaDeNegocioViolada("El remito requiere un depósito para descontar stock")

    def validar_conversion_a_factura(self, tipo: str, estado: str) -> None:
        if tipo != "remito":
            raise ReglaDeNegocioViolada("Solo se puede facturar un remito")
        if estado != "confirmado":
            raise ReglaDeNegocioViolada("El remito debe estar confirmado para facturarlo")

    @staticmethod
    def calcular_importes(
        lineas: list[tuple[int, float]], iva_porcentaje: float
    ) -> tuple[float, float, float]:
        """Devuelve (neto, iva, total) redondeados a 2 decimales."""
        neto = round(sum(cantidad * precio for cantidad, precio in lineas), 2)
        iva = round(neto * (iva_porcentaje / 100.0), 2)
        total = round(neto + iva, 2)
        return neto, iva, total

    @staticmethod
    def calcular_total(lineas: list[tuple[int, float]]) -> float:
        """Compat: suma neta (sin IVA) de líneas."""
        return round(sum(cantidad * precio for cantidad, precio in lineas), 2)
