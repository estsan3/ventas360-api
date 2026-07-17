"""Tests unitarios BO cxc / cobranzas."""

import pytest

from app.core.excepciones import ReglaDeNegocioViolada
from app.modulos.cobranzas.bo import CobranzasBO
from app.modulos.cxc.bo import CxcBO


def test_saldo_debe_haber() -> None:
    assert CxcBO.calcular_saldo(1000.0, 300.0) == 700.0


def test_movimiento_monto_invalido() -> None:
    with pytest.raises(ReglaDeNegocioViolada, match="mayor a cero"):
        CxcBO().validar_movimiento("debe", 0)


def test_recibo_imputaciones_cuadran() -> None:
    CobranzasBO().validar_recibo(100.0, [60.0, 40.0])


def test_recibo_imputaciones_no_cuadran() -> None:
    with pytest.raises(ReglaDeNegocioViolada, match="igualar"):
        CobranzasBO().validar_recibo(100.0, [50.0, 40.0])
