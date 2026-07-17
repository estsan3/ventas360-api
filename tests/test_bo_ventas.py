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


def test_transicion_borrador_a_confirmado(bo: VentasBO) -> None:
    bo.validar_transicion("borrador", "confirmado")


def test_transicion_invalida(bo: VentasBO) -> None:
    with pytest.raises(ReglaDeNegocioViolada, match="No se puede pasar"):
        bo.validar_transicion("entregado", "borrador")


def test_transicion_mismo_estado(bo: VentasBO) -> None:
    with pytest.raises(ReglaDeNegocioViolada, match="ya está en estado"):
        bo.validar_transicion("confirmado", "confirmado")


def test_calcular_total() -> None:
    assert VentasBO.calcular_total([(2, 10.0), (1, 5.5)]) == 25.5
