"""Capa BO del módulo ventas: reglas puras (sin DB, sin HTTP)."""

from app.core.excepciones import ReglaDeNegocioViolada

_TRANSICIONES: dict[str, set[str]] = {
    "borrador": {"confirmado", "cancelado"},
    "confirmado": {"entregado", "cancelado"},
    "entregado": set(),
    "cancelado": set(),
}


class VentasBO:
    """Reglas de negocio de pedidos."""

    def validar_creacion(self, cantidad_lineas: int) -> None:
        if cantidad_lineas < 1:
            raise ReglaDeNegocioViolada("El pedido debe tener al menos una línea")

    def validar_cantidad(self, cantidad: int) -> None:
        if cantidad <= 0:
            raise ReglaDeNegocioViolada("La cantidad debe ser mayor a cero")

    def validar_transicion(self, estado_actual: str, nuevo_estado: str) -> None:
        if nuevo_estado == estado_actual:
            raise ReglaDeNegocioViolada(f"El pedido ya está en estado {nuevo_estado}")
        permitidos = _TRANSICIONES.get(estado_actual, set())
        if nuevo_estado not in permitidos:
            raise ReglaDeNegocioViolada(
                f"No se puede pasar de {estado_actual} a {nuevo_estado}"
            )

    @staticmethod
    def calcular_total(lineas: list[tuple[int, float]]) -> float:
        """Suma cantidad × precio_unitario de cada línea."""
        return round(sum(cantidad * precio for cantidad, precio in lineas), 2)
