"""BO del módulo bancos."""

from app.core.excepciones import ReglaDeNegocioViolada

TIPOS_MOV = {"credito", "debito"}
TIPOS_VALOR = {"cheque_tercero", "cheque_propio"}
ESTADOS_VALOR = {"en_cartera", "depositado", "cobrado", "rechazado"}


class BancosBO:
    def validar_movimiento(self, tipo: str, monto: float) -> None:
        if tipo not in TIPOS_MOV:
            raise ReglaDeNegocioViolada(f"Tipo bancario inválido: {tipo}")
        if monto <= 0:
            raise ReglaDeNegocioViolada("El monto debe ser mayor a cero")

    def validar_valor(self, tipo: str, monto: float) -> None:
        if tipo not in TIPOS_VALOR:
            raise ReglaDeNegocioViolada(f"Tipo de valor inválido: {tipo}")
        if monto <= 0:
            raise ReglaDeNegocioViolada("El monto del valor debe ser mayor a cero")

    def validar_deposito(self, estado: str) -> None:
        if estado != "en_cartera":
            raise ReglaDeNegocioViolada(
                "Solo se depositan valores en cartera"
            )

    @staticmethod
    def calcular_saldo(creditos: float, debitos: float) -> float:
        return round(creditos - debitos, 2)
