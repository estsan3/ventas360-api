"""Tests unitarios del BO de compras."""

import pytest

from app.core.excepciones import ReglaDeNegocioViolada
from app.modulos.compras.bo import ComprasBO


def test_tipo_invalido() -> None:
    with pytest.raises(ReglaDeNegocioViolada, match="inválido"):
        ComprasBO().validar_tipo("oc")


def test_importes() -> None:
    neto, iva, total = ComprasBO().calcular_importes(100.0, 21.0)
    assert neto == 100.0
    assert iva == 21.0
    assert total == 121.0


def test_confirmacion_sin_deposito() -> None:
    with pytest.raises(ReglaDeNegocioViolada, match="deposito"):
        ComprasBO().validar_confirmacion("remito_compra", "borrador", None)


def test_facturar_solo_remito_confirmado() -> None:
    with pytest.raises(ReglaDeNegocioViolada, match="confirmado"):
        ComprasBO().validar_conversion_a_factura("remito_compra", "borrador")
