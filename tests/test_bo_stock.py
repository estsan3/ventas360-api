"""Tests unitarios del BO de stock."""

import pytest

from app.core.excepciones import ReglaDeNegocioViolada
from app.modulos.stock.bo import StockBO


def test_ajuste_cero() -> None:
    with pytest.raises(ReglaDeNegocioViolada, match="distinto de cero"):
        StockBO().validar_ajuste(0, 10)


def test_ajuste_deja_negativo() -> None:
    with pytest.raises(ReglaDeNegocioViolada, match="insuficiente"):
        StockBO().validar_ajuste(-5, 3)


def test_egreso_ok() -> None:
    StockBO().validar_egreso(3, 10)


def test_egreso_sin_stock() -> None:
    with pytest.raises(ReglaDeNegocioViolada, match="insuficiente"):
        StockBO().validar_egreso(5, 2)
