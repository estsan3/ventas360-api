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


def test_recibo_imputaciones_a_cuenta() -> None:
    CobranzasBO().validar_recibo(100.0, [50.0, 40.0])


def test_recibo_anticipo_sin_imputar() -> None:
    CobranzasBO().validar_recibo(100.0, [])


def test_recibo_imputaciones_superan_monto() -> None:
    with pytest.raises(ReglaDeNegocioViolada, match="superar"):
        CobranzasBO().validar_recibo(100.0, [60.0, 50.0])


def test_medios_mixtos_persisten_como_mixto() -> None:
    from app.modulos.bancos.schemas import DatosChequeRequest
    from app.modulos.cobranzas.bo import LineaMedio

    lineas = [
        LineaMedio(medio="efectivo", monto=40.0, cheque=None),
        LineaMedio(
            medio="cheque",
            monto=60.0,
            cheque=DatosChequeRequest(numero="1001", banco_emisor="Galicia"),
        ),
    ]
    assert CobranzasBO().validar_medios(100.0, lineas) == "mixto"


def test_medios_mas_de_tres_cheques() -> None:
    from app.modulos.bancos.schemas import DatosChequeRequest
    from app.modulos.cobranzas.bo import LineaMedio

    ch = DatosChequeRequest(numero="1", banco_emisor="Nación")
    lineas = [
        LineaMedio(medio="cheque", monto=10.0, cheque=ch) for _ in range(4)
    ]
    with pytest.raises(ReglaDeNegocioViolada, match="cheques"):
        CobranzasBO().validar_medios(40.0, lineas)
