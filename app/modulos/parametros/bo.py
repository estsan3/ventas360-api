"""BO del módulo parámetros."""

from app.core.excepciones import ReglaDeNegocioViolada

TIPOS_TALONARIO = {"pedido", "remito", "factura"}


class ParametrosBO:
    def validar_talonario(self, tipo: str, proximo_numero: int) -> None:
        if tipo not in TIPOS_TALONARIO:
            raise ReglaDeNegocioViolada(f"Tipo de talonario inválido: {tipo}")
        if proximo_numero < 1:
            raise ReglaDeNegocioViolada("El próximo número debe ser ≥ 1")

    @staticmethod
    def formatear_numero(prefijo: str, numero: int) -> str:
        cuerpo = f"{numero:08d}"
        return f"{prefijo}{cuerpo}" if prefijo else cuerpo
