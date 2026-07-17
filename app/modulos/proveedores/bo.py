"""BO del módulo proveedores."""

import re

from app.core.excepciones import ReglaDeNegocioViolada
from app.modulos.proveedores.excel import normalizar_campo

CONDICIONES_IVA = {
    "responsable_inscripto",
    "monotributo",
    "exento",
    "consumidor_final",
}

POLITICAS_PRECIO = {"solo_costo", "margen_fijo", "copiar_lista"}

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

    def validar_mapeo(self, mapeo: list[dict[str, str]]) -> list[dict[str, str]]:
        if not mapeo:
            raise ReglaDeNegocioViolada("El mapeo de columnas es obligatorio")
        normalizado: list[dict[str, str]] = []
        vistos: set[str] = set()
        for item in mapeo:
            campo = normalizar_campo(item.get("campo", ""))
            columna = (item.get("columna") or "").strip()
            if not columna:
                raise ReglaDeNegocioViolada("Cada fila de mapeo requiere columna")
            if campo != "ignorar":
                if campo in vistos:
                    raise ReglaDeNegocioViolada(f"Campo duplicado en mapeo: {campo}")
                vistos.add(campo)
            normalizado.append({"columna": columna.upper().replace("COLUMNA ", ""), "campo": campo})
        if "codigo_producto" not in vistos:
            raise ReglaDeNegocioViolada("El mapeo debe incluir Código de producto")
        if "precio_costo" not in vistos:
            raise ReglaDeNegocioViolada("El mapeo debe incluir Precio de costo")
        return normalizado

    def validar_politica(self, politica: str) -> None:
        if politica not in POLITICAS_PRECIO:
            raise ReglaDeNegocioViolada(f"Política de precio inválida: {politica}")

    def resolver_precio_venta(
        self,
        *,
        politica: str,
        costo: float,
        precio_lista: float | None,
        margen_pct: float,
    ) -> tuple[float | None, bool]:
        """Devuelve (precio_venta, actualizar_precio).

        - solo_costo: no toca precio en updates; en altas el contrato usa costo.
        - margen_fijo: costo * (1 + margen/100)
        - copiar_lista: usa precio_lista del Excel
        """
        if politica == "solo_costo":
            return None, False
        if politica == "margen_fijo":
            return round(costo * (1 + margen_pct / 100.0), 2), True
        if politica == "copiar_lista":
            if precio_lista is None or precio_lista <= 0:
                return None, False
            return precio_lista, True
        raise ReglaDeNegocioViolada(f"Política de precio inválida: {politica}")
