"""Capa BO del módulo clientes: reglas puras (sin DB, sin HTTP)."""

from app.core.excepciones import ReglaDeNegocioViolada


class ClienteBO:
    """Reglas de negocio de clientes."""

    def validar_alta(self, email_ya_registrado: bool) -> None:
        if email_ya_registrado:
            raise ReglaDeNegocioViolada("Ya existe un cliente con ese email")

    def validar_baja(self, activo: bool) -> None:
        if not activo:
            raise ReglaDeNegocioViolada("El cliente ya está inactivo")
