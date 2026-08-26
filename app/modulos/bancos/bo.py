"""BO del módulo bancos."""

from app.core.excepciones import ReglaDeNegocioViolada

TIPOS_MOV = {"credito", "debito"}
TIPOS_VALOR = {"cheque_tercero", "cheque_propio"}
ESTADOS_VALOR = {"en_cartera", "depositado", "cobrado", "rechazado", "entregado"}


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

    def validar_cheque(self, numero: str, banco_emisor: str, monto: float) -> None:
        if not (numero or "").strip():
            raise ReglaDeNegocioViolada("El cheque necesita número")
        if not (banco_emisor or "").strip():
            raise ReglaDeNegocioViolada("El cheque necesita banco emisor")
        self.validar_valor("cheque_tercero", monto)

    def validar_deposito(self, estado: str) -> None:
        if estado != "en_cartera":
            raise ReglaDeNegocioViolada("Solo se depositan valores en cartera")

    def validar_entrega(self, estado: str) -> None:
        if estado != "en_cartera":
            raise ReglaDeNegocioViolada("Solo se entregan valores en cartera")

    def validar_destinatario(self, destinatario: str) -> None:
        if len((destinatario or "").strip()) < 2:
            raise ReglaDeNegocioViolada("Indicá a quién se entrega el cheque")

    @staticmethod
    def calcular_saldo(creditos: float, debitos: float) -> float:
        return round(creditos - debitos, 2)
