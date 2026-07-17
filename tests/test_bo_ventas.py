"""Tests unitarios del BO de ventas (sin DB)."""

import pytest

from app.core.excepciones import ReglaDeNegocioViolada
from app.modulos.ventas.bo import VentasBO


@pytest.fixture
def bo() -> VentasBO:
    return VentasBO()


def test_validar_creacion_requiere_lineas(bo: VentasBO) -> None:
    with pytest.raises(ReglaDeNegocioViolada, match="al menos una línea"):
        bo.validar_creacion(0)


def test_validar_cantidad_positiva(bo: VentasBO) -> None:
    with pytest.raises(ReglaDeNegocioViolada, match="mayor a cero"):
        bo.validar_cantidad(0)


def test_transicion_pedido_ok(bo: VentasBO) -> None:
    bo.validar_transicion("pedido", "borrador", "confirmado")


def test_transicion_remito_a_facturado(bo: VentasBO) -> None:
    bo.validar_transicion("remito", "confirmado", "facturado")


def test_transicion_invalida(bo: VentasBO) -> None:
    with pytest.raises(ReglaDeNegocioViolada, match="No se puede pasar"):
        bo.validar_transicion("factura", "confirmado", "borrador")


def test_confirmacion_remito_sin_deposito(bo: VentasBO) -> None:
    with pytest.raises(ReglaDeNegocioViolada, match="depósito"):
        bo.validar_confirmacion_remito("remito", "borrador", None)


def test_conversion_requiere_confirmado(bo: VentasBO) -> None:
    with pytest.raises(ReglaDeNegocioViolada, match="confirmado"):
        bo.validar_conversion_a_factura("remito", "borrador")


def test_calcular_importes_con_iva() -> None:
    neto, iva, total = VentasBO.calcular_importes([(2, 100.0)], 21.0)
    assert neto == 200.0
    assert iva == 42.0
    assert total == 242.0
