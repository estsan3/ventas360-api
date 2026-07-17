"""Capa BO del módulo clientes: reglas puras."""

from app.core.excepciones import ReglaDeNegocioViolada
from app.modulos.clientes.models import Cliente


class ClienteBO:
    """Reglas de negocio de clientes."""

    def validar_alta(self, email_ya_registrado: bool) -> None:
        if email_ya_registrado:
            raise ReglaDeNegocioViolada("Ya existe un cliente con ese email")

    def validar_baja(self, cliente: Cliente) -> None:
        if not cliente.activo:
            raise ReglaDeNegocioViolada("El cliente ya está inactivo")
