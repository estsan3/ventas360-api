"""Capa BO del módulo clientes: reglas puras (sin DB, sin HTTP)."""

import re

from app.core.excepciones import ReglaDeNegocioViolada

CONDICIONES_IVA = {
    "responsable_inscripto",
    "monotributo",
    "exento",
    "consumidor_final",
}

_CUIT_DIGITOS = re.compile(r"^\d{11}$")


class ClienteBO:
    """Reglas de negocio de clientes."""

    def validar_alta(self, email_ya_registrado: bool) -> None:
        if email_ya_registrado:
            raise ReglaDeNegocioViolada("Ya existe un cliente con ese email")

    def validar_baja(self, activo: bool) -> None:
        if not activo:
            raise ReglaDeNegocioViolada("El cliente ya está inactivo")

    def validar_datos_comerciales(
        self,
        cuit: str,
        condicion_iva: str,
        limite_credito: float,
    ) -> None:
        if condicion_iva not in CONDICIONES_IVA:
            raise ReglaDeNegocioViolada(f"Condición IVA inválida: {condicion_iva}")
        if limite_credito < 0:
            raise ReglaDeNegocioViolada("El límite de crédito no puede ser negativo")
        cuit_limpio = cuit.replace("-", "").strip()
        if cuit_limpio and not _CUIT_DIGITOS.match(cuit_limpio):
            raise ReglaDeNegocioViolada("El CUIT debe tener 11 dígitos")

    def validar_vendedor(self, vendedor_id: str | None, vendedor_existe: bool) -> None:
        if vendedor_id and not vendedor_existe:
            raise ReglaDeNegocioViolada("El vendedor indicado no existe")
