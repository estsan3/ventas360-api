"""BO del módulo parámetros."""

import re

from app.core.excepciones import ReglaDeNegocioViolada

TIPOS_TALONARIO = {"pedido", "remito", "factura"}
CONDICIONES_IVA_EMISOR = {"responsable_inscripto", "monotributo", "exento"}
_CUIT_DIGITOS = re.compile(r"^\d{11}$")


class ParametrosBO:
    def validar_talonario(self, tipo: str, proximo_numero: int) -> None:
        if tipo not in TIPOS_TALONARIO:
            raise ReglaDeNegocioViolada(f"Tipo de talonario inválido: {tipo}")
        if proximo_numero < 1:
            raise ReglaDeNegocioViolada("El próximo número debe ser ≥ 1")

    def validar_afip(
        self,
        *,
        habilitada: bool,
        cuit: str,
        condicion_iva: str,
        punto_venta: int,
    ) -> str:
        """Valida identidad fiscal. Devuelve CUIT limpio (11 dígitos o vacío)."""
        if condicion_iva not in CONDICIONES_IVA_EMISOR:
            raise ReglaDeNegocioViolada(f"Condición IVA del emisor inválida: {condicion_iva}")
        if punto_venta < 1 or punto_venta > 99999:
            raise ReglaDeNegocioViolada("El punto de venta ARCA debe estar entre 1 y 99999")
        cuit_limpio = "".join(ch for ch in cuit if ch.isdigit())
        if cuit_limpio and not _CUIT_DIGITOS.match(cuit_limpio):
            raise ReglaDeNegocioViolada("El CUIT del emisor debe tener 11 dígitos")
        if habilitada and not cuit_limpio:
            raise ReglaDeNegocioViolada(
                "Para habilitar ARCA hay que cargar el CUIT del emisor (11 dígitos)"
            )
        return cuit_limpio

    @staticmethod
    def formatear_numero(prefijo: str, numero: int) -> str:
        cuerpo = f"{numero:08d}"
        return f"{prefijo}{cuerpo}" if prefijo else cuerpo
