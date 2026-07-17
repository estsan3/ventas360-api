"""Tests unitarios del BO de caja."""

import pytest

from app.core.excepciones import ReglaDeNegocioViolada
from app.modulos.caja.bo import CajaBO


def test_medio_invalido() -> None:
    with pytest.raises(ReglaDeNegocioViolada, match="Medio"):
        CajaBO().validar_movimiento("ingreso", "crypto", 100)


def test_saldo() -> None:
    assert CajaBO.calcular_saldo(100, 40) == 60.0
