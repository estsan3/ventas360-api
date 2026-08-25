"""Capa BO del módulo auth: reglas de negocio puras (sin DB, sin HTTP)."""

from app.core.excepciones import NoAutenticado, ReglaDeNegocioViolada
from app.core.seguridad import verificar_password

ROLES_VALIDOS = {"administrador", "encargado", "vendedor"}


class UsuarioBO:
    """Reglas de negocio sobre usuarios y credenciales."""

    def validar_credenciales(self, password_hash: str | None, password: str) -> None:
        """Verifica que exista hash y que la contraseña coincida.

        Mismo mensaje en ambos fallos para no revelar si el email está registrado.
        """
        if password_hash is None or not verificar_password(password, password_hash):
            raise NoAutenticado("Email o contraseña incorrectos")

    def validar_alta(self, email_ya_registrado: bool, rol: str) -> None:
        if email_ya_registrado:
            raise ReglaDeNegocioViolada("Ya existe un usuario con ese email")
        if rol not in ROLES_VALIDOS:
            raise ReglaDeNegocioViolada(f"Rol inválido: {rol}")

    def validar_baja(
        self, es_el_mismo_usuario: bool, es_ultimo_administrador: bool
    ) -> None:
        if es_el_mismo_usuario:
            raise ReglaDeNegocioViolada("No podés darte de baja a vos mismo")
        if es_ultimo_administrador:
            raise ReglaDeNegocioViolada("No se puede eliminar al último administrador")

    def validar_login_host(
        self,
        *,
        tenant_id_usuario: str | None,
        rol: str,
        tipo_host: str,
        tenant_id_host: str | None,
    ) -> None:
        """El usuario solo entra en el host de su comercio (o admin.* si es superadmin)."""
        if tipo_host == "plataforma":
            if rol != "superadmin" or tenant_id_usuario is not None:
                raise NoAutenticado(
                    "El acceso a la plataforma es solo para superadmin"
                )
            return
        if tipo_host != "comercio" or not tenant_id_host:
            raise NoAutenticado(
                "Entrá con el subdominio de tu comercio "
                "(ej. agronorte.localhost:4201)."
            )
        if tenant_id_usuario != tenant_id_host:
            raise NoAutenticado("Este usuario no pertenece a este comercio")
