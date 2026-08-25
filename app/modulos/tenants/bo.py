"""BO del módulo tenants: slug, nombre y clasificación de host (sin DB)."""

import re

from app.core.excepciones import ReglaDeNegocioViolada

# Primera etiqueta del host reservada para la plataforma (no es un comercio).
SLUG_PLATAFORMA_DEFAULT = "admin"
SLUGS_RESERVADOS = frozenset(
    {SLUG_PLATAFORMA_DEFAULT, "www", "api", "app", "localhost", "mail"}
)
_SLUG_RE = re.compile(r"^[a-z0-9]([a-z0-9-]{0,46}[a-z0-9])?$")
_IPV4_RE = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}$")

TIPO_PLATAFORMA = "plataforma"
TIPO_COMERCIO = "comercio"
TIPO_SIN_SLUG = "sin_slug"

MODULO_CONFIGURACION = "configuracion"
MODULOS_MATRIZ = (
    "inicio",
    "mostrador",
    "cta_cte",
    "articulos",
    "stock",
    "clientes",
    "ventas",
    "compras",
)
ETIQUETAS_MODULO = {
    "inicio": "Inicio",
    "mostrador": "Mostrador",
    "cta_cte": "Cta. cte.",
    "articulos": "Artículos",
    "stock": "Stock",
    "clientes": "Clientes",
    "ventas": "Presup. / Pedidos / Remitos",
    "compras": "Compras / Caja / Bancos",
}
ROLES_EDITABLES = ("vendedor", "encargado")
ROL_ADMINISTRADOR = "administrador"
DEFAULTS_HABILITADOS: dict[str, frozenset[str]] = {
    "vendedor": frozenset({"inicio", "mostrador", "cta_cte"}),
    "encargado": frozenset({"inicio", "mostrador", "cta_cte", "articulos", "stock"}),
}


class TenantsBO:
    """Reglas de slug, nombre comercial y lectura del Host/Origin."""

    def validar_nombre(self, nombre: str) -> None:
        if not nombre.strip():
            raise ReglaDeNegocioViolada("El nombre del comercio es obligatorio")

    def normalizar_slug(self, slug: str) -> str:
        return slug.strip().lower()

    def validar_slug(self, slug: str, slug_plataforma: str = SLUG_PLATAFORMA_DEFAULT) -> str:
        normalizado = self.normalizar_slug(slug)
        if not _SLUG_RE.fullmatch(normalizado):
            raise ReglaDeNegocioViolada(
                "El slug debe ser minúsculas, números y guiones "
                "(ej. agronorte, kiosco-milka)"
            )
        reservados = SLUGS_RESERVADOS | {slug_plataforma.strip().lower()}
        if normalizado in reservados:
            raise ReglaDeNegocioViolada(f"El slug '{normalizado}' está reservado")
        return normalizado

    def extraer_etiqueta(self, host: str) -> str:
        """Primera etiqueta de `demo.localhost:4201` → `demo`."""
        hostname = host.strip().lower()
        if not hostname:
            return ""
        if "://" in hostname:
            hostname = hostname.split("://", 1)[1]
        hostname = hostname.split("/", 1)[0]
        hostname = hostname.split("@")[-1]
        if hostname.startswith("["):
            return ""
        hostname = hostname.split(":", 1)[0]
        if hostname in {"localhost", "test"} or _IPV4_RE.match(hostname):
            return ""
        partes = [p for p in hostname.split(".") if p]
        return partes[0] if partes else ""

    def clasificar_host(
        self, host: str, slug_plataforma: str = SLUG_PLATAFORMA_DEFAULT
    ) -> tuple[str, str | None]:
        """Devuelve (tipo, slug|None): plataforma, comercio o sin_slug."""
        etiqueta = self.extraer_etiqueta(host)
        plataforma = slug_plataforma.strip().lower() or SLUG_PLATAFORMA_DEFAULT
        if not etiqueta:
            return TIPO_SIN_SLUG, None
        if etiqueta == plataforma:
            return TIPO_PLATAFORMA, None
        return TIPO_COMERCIO, etiqueta

    def resolver_modulos(
        self, rol: str, filas_rol: dict[str, bool] | None
    ) -> list[str]:
        """Módulos habilitados para el rol. Admin siempre todo (incluida Config)."""
        if rol == "superadmin":
            return []
        if rol == ROL_ADMINISTRADOR:
            return [*MODULOS_MATRIZ, MODULO_CONFIGURACION]
        defaults = DEFAULTS_HABILITADOS.get(rol, frozenset())
        if not filas_rol:
            return [m for m in MODULOS_MATRIZ if m in defaults]
        return [m for m in MODULOS_MATRIZ if filas_rol.get(m, False)]

    def validar_actualizacion_permisos(
        self, rol: str, modulos: dict[str, bool]
    ) -> None:
        if rol not in ROLES_EDITABLES:
            raise ReglaDeNegocioViolada(
                "Solo se editan los permisos de Vendedor y Encargado"
            )
        desconocidos = [m for m in modulos if m not in MODULOS_MATRIZ]
        if desconocidos:
            raise ReglaDeNegocioViolada(
                f"Módulo no configurable: {desconocidos[0]}"
            )

    def celdas_default(self) -> list[tuple[str, str, bool, bool]]:
        """(modulo, etiqueta, vendedor, encargado) para armar la matriz."""
        vend = DEFAULTS_HABILITADOS["vendedor"]
        enc = DEFAULTS_HABILITADOS["encargado"]
        return [
            (m, ETIQUETAS_MODULO[m], m in vend, m in enc) for m in MODULOS_MATRIZ
        ]
