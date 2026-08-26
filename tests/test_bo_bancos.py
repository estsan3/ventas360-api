"""Tests unitarios del BO de bancos."""

import pytest

from app.core.excepciones import ReglaDeNegocioViolada
from app.modulos.bancos.bo import BancosBO


def test_deposito_solo_en_cartera() -> None:
    with pytest.raises(ReglaDeNegocioViolada, match="cartera"):
        BancosBO().validar_deposito("depositado")


def test_cheque_exige_numero_y_banco() -> None:
    with pytest.raises(ReglaDeNegocioViolada, match="número"):
        BancosBO().validar_cheque("", "Galicia", 100)
    with pytest.raises(ReglaDeNegocioViolada, match="banco"):
        BancosBO().validar_cheque("123", "", 100)


def test_entrega_solo_en_cartera() -> None:
    with pytest.raises(ReglaDeNegocioViolada, match="cartera"):
        BancosBO().validar_entrega("depositado")


def test_saldo_cuenta() -> None:
    assert BancosBO.calcular_saldo(500, 120) == 380.0
