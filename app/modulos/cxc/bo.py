"""BO del módulo cxc."""

from app.core.excepciones import ReglaDeNegocioViolada

TIPOS = {"debe", "haber"}


class CxcBO:
    def validar_movimiento(self, tipo: str, monto: float) -> None:
        if tipo not in TIPOS:
            raise ReglaDeNegocioViolada(f"Tipo de movimiento inválido: {tipo}")
        if monto <= 0:
            raise ReglaDeNegocioViolada("El monto debe ser mayor a cero")

    @staticmethod
    def calcular_saldo(debe_total: float, haber_total: float) -> float:
        return round(debe_total - haber_total, 2)
