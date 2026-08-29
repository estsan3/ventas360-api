"""Tests unitarios del BO de compras."""

import pytest

from app.core.excepciones import ReglaDeNegocioViolada
from app.modulos.compras.bo import ComprasBO


def test_tipo_invalido() -> None:
    with pytest.raises(ReglaDeNegocioViolada, match="inválido"):
        ComprasBO().validar_tipo("oc")


def test_tipo_pedido_valido() -> None:
    ComprasBO().validar_tipo("pedido_compra")


def test_importes() -> None:
    neto, iva, total = ComprasBO().calcular_importes(100.0, 21.0)
    assert neto == 100.0
    assert iva == 21.0
    assert total == 121.0


def test_confirmacion_sin_deposito() -> None:
    with pytest.raises(ReglaDeNegocioViolada, match="deposito"):
        ComprasBO().validar_confirmacion("remito_compra", "borrador", None)


def test_no_confirmar_pedido() -> None:
    with pytest.raises(ReglaDeNegocioViolada, match="no ingresa stock"):
        ComprasBO().validar_confirmacion("pedido_compra", "borrador", "dep-1")


def test_emitir_solo_borrador() -> None:
    with pytest.raises(ReglaDeNegocioViolada, match="borrador"):
        ComprasBO().validar_emitir_pedido("pedido_compra", "emitido")


def test_estado_pedido_parcial() -> None:
    assert ComprasBO().estado_pedido_segun_recepcion(10, 4) == "parcial"
    assert ComprasBO().estado_pedido_segun_recepcion(10, 10) == "recibido"
    assert ComprasBO().estado_pedido_segun_recepcion(10, 0) == "emitido"


def test_facturar_solo_remito_confirmado() -> None:
    with pytest.raises(ReglaDeNegocioViolada, match="confirmado"):
        ComprasBO().validar_conversion_a_factura("remito_compra", "borrador")


def test_linea_requiere_identidad() -> None:
    with pytest.raises(ReglaDeNegocioViolada, match="artículo"):
        ComprasBO().validar_linea(None, None)
