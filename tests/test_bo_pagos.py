"""BO de pagos a proveedores."""

from app.modulos.pagos.bo import LineaMedioPago, PagosBO


def test_suma_de_medios_debe_igualar_monto() -> None:
    bo = PagosBO()
    try:
        bo.validar_medios(
            100,
            [
                LineaMedioPago("efectivo", 40, "", None),
                LineaMedioPago("transferencia", 50, "", None),
            ],
        )
        raise AssertionError("debía fallar")
    except Exception as exc:
        assert "igualar" in str(exc).lower()


def test_cheque_sin_cartera_ni_propio_falla() -> None:
    bo = PagosBO()
    try:
        bo.validar_medios(80, [LineaMedioPago("cheque", 80, "", None)])
        raise AssertionError("debía fallar")
    except Exception as exc:
        assert "cheque" in str(exc).lower()


def test_un_medio_devuelve_ese_medio() -> None:
    bo = PagosBO()
    assert (
        bo.validar_medios(50, [LineaMedioPago("efectivo", 50, "", None)]) == "efectivo"
    )
