"""BO del módulo caja."""

from app.core.excepciones import ReglaDeNegocioViolada

TIPOS = {"ingreso", "egreso"}
MEDIOS = {"efectivo", "tarjeta", "otro"}


class CajaBO:
    def validar_movimiento(self, tipo: str, medio: str, monto: float) -> None:
        if tipo not in TIPOS:
            raise ReglaDeNegocioViolada(f"Tipo de caja inválido: {tipo}")
        if medio not in MEDIOS:
            raise ReglaDeNegocioViolada(f"Medio de caja inválido: {medio}")
        if monto <= 0:
            raise ReglaDeNegocioViolada("El monto debe ser mayor a cero")

    @staticmethod
    def calcular_saldo(ingresos: float, egresos: float) -> float:
        return round(ingresos - egresos, 2)
