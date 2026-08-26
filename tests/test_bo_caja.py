"""Tests unitarios del BO de caja."""

import pytest

from app.core.excepciones import ReglaDeNegocioViolada
from app.modulos.caja.bo import CajaBO


def test_medio_invalido() -> None:
    with pytest.raises(ReglaDeNegocioViolada, match="Medio"):
        CajaBO().validar_movimiento("ingreso", "crypto", 100)


def test_medio_cheque_valido() -> None:
    CajaBO().validar_movimiento("ingreso", "cheque", 100)


def test_ingreso_cheque_exige_datos() -> None:
    with pytest.raises(ReglaDeNegocioViolada, match="datos del cheque"):
        CajaBO().validar_datos_cheque("ingreso", None, False)


def test_saldo() -> None:
    assert CajaBO.calcular_saldo(100, 40) == 60.0


def test_no_abre_si_ya_existe() -> None:
    with pytest.raises(ReglaDeNegocioViolada, match="abierta"):
        CajaBO().validar_apertura(type("S", (), {"estado": "abierta"})())


def test_diferencia_arqueo() -> None:
    assert CajaBO.calcular_diferencia(1000, 980) == -20.0
    assert CajaBO.calcular_diferencia(1000, 1010) == 10.0


def test_egreso_sin_efectivo() -> None:
    with pytest.raises(ReglaDeNegocioViolada, match="suficiente"):
        CajaBO().validar_egreso_efectivo(50, 40)
