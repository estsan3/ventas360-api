"""Tests unitarios del BO de bancos."""

import pytest

from app.core.excepciones import ReglaDeNegocioViolada
from app.modulos.bancos.bo import BancosBO


def test_deposito_solo_en_cartera() -> None:
    with pytest.raises(ReglaDeNegocioViolada, match="cartera"):
        BancosBO().validar_deposito("depositado")


def test_saldo_cuenta() -> None:
    assert BancosBO.calcular_saldo(500, 120) == 380.0
