"""BO del módulo stock: reglas puras."""

from app.core.excepciones import ReglaDeNegocioViolada

TIPOS_MOVIMIENTO = {"ajuste", "egreso_remito", "ingreso"}


class StockBO:
    def validar_ajuste(self, cantidad_delta: int, saldo_actual: int) -> None:
        if cantidad_delta == 0:
            raise ReglaDeNegocioViolada("El ajuste debe ser distinto de cero")
        nuevo = saldo_actual + cantidad_delta
        if nuevo < 0:
            raise ReglaDeNegocioViolada(
                f"Stock insuficiente: saldo {saldo_actual}, ajuste {cantidad_delta}"
            )

    def validar_egreso(self, cantidad: int, saldo_actual: int) -> None:
        if cantidad <= 0:
            raise ReglaDeNegocioViolada("La cantidad a egresar debe ser mayor a cero")
        if saldo_actual < cantidad:
            raise ReglaDeNegocioViolada(
                f"Stock insuficiente: disponible {saldo_actual}, solicitado {cantidad}"
            )

    def validar_ingreso(self, cantidad: int) -> None:
        if cantidad <= 0:
            raise ReglaDeNegocioViolada("La cantidad a ingresar debe ser mayor a cero")
