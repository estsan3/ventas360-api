"""Tests unitarios del BO de proveedores."""

import pytest

from app.core.excepciones import ReglaDeNegocioViolada
from app.modulos.proveedores.bo import ProveedorBO


def test_cuit_invalido() -> None:
    with pytest.raises(ReglaDeNegocioViolada, match="CUIT"):
        ProveedorBO().validar_datos("123", "responsable_inscripto", "Acme")


def test_datos_ok() -> None:
    ProveedorBO().validar_datos("30711222334", "responsable_inscripto", "Acme")
