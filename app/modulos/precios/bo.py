"""BO del módulo precios."""

from app.core.excepciones import ReglaDeNegocioViolada


class PreciosBO:
    def validar_precio(self, precio: float) -> None:
        if precio <= 0:
            raise ReglaDeNegocioViolada("El precio debe ser mayor a cero")
