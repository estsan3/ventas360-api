"""Tests unitarios del BO de zonas."""

import pytest

from app.core.excepciones import ReglaDeNegocioViolada
from app.modulos.zonas.bo import ZonaBO


@pytest.fixture
def bo() -> ZonaBO:
    return ZonaBO()


def test_validar_nombre_vacio(bo: ZonaBO) -> None:
    with pytest.raises(ReglaDeNegocioViolada, match="obligatorio"):
        bo.validar_nombre("   ")


def test_validar_baja_ya_inactiva(bo: ZonaBO) -> None:
    with pytest.raises(ReglaDeNegocioViolada, match="inactiva"):
        bo.validar_baja(False)


def test_validar_ok(bo: ZonaBO) -> None:
    bo.validar_nombre("Centro")
    bo.validar_baja(True)
