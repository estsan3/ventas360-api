"""Capa BO del módulo productos: reglas puras."""

from app.core.excepciones import ReglaDeNegocioViolada


class ProductoBO:
    """Reglas de negocio de productos."""

    def validar_alta(self, sku_ya_registrado: bool) -> None:
        if sku_ya_registrado:
            raise ReglaDeNegocioViolada("Ya existe un producto con ese SKU")

    def validar_stock(self, stock: int) -> None:
        if stock < 0:
            raise ReglaDeNegocioViolada("El stock no puede ser negativo")
