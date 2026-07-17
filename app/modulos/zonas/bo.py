"""BO del módulo zonas."""

from app.core.excepciones import ReglaDeNegocioViolada


class ZonaBO:
    def validar_nombre(self, nombre: str) -> None:
        if not nombre.strip():
            raise ReglaDeNegocioViolada("El nombre de la zona es obligatorio")

    def validar_baja(self, activo: bool) -> None:
        if not activo:
            raise ReglaDeNegocioViolada("La zona ya está inactiva")
