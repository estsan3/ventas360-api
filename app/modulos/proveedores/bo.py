"""BO del módulo proveedores."""

import re

from app.core.excepciones import ReglaDeNegocioViolada

CONDICIONES_IVA = {
    "responsable_inscripto",
    "monotributo",
    "exento",
    "consumidor_final",
}

_CUIT_DIGITOS = re.compile(r"^\d{11}$")


class ProveedorBO:
    def validar_datos(
        self, cuit: str, condicion_iva: str, nombre: str
    ) -> None:
        if not nombre.strip():
            raise ReglaDeNegocioViolada("El nombre del proveedor es obligatorio")
        if condicion_iva not in CONDICIONES_IVA:
            raise ReglaDeNegocioViolada(f"Condición IVA inválida: {condicion_iva}")
        cuit_limpio = cuit.replace("-", "").strip()
        if cuit_limpio and not _CUIT_DIGITOS.match(cuit_limpio):
            raise ReglaDeNegocioViolada("El CUIT debe tener 11 dígitos")

    def validar_baja(self, activo: bool) -> None:
        if not activo:
            raise ReglaDeNegocioViolada("El proveedor ya está inactivo")
