"""Tests unitarios del BO de clientes (sin DB)."""

import pytest

from app.core.excepciones import ReglaDeNegocioViolada
from app.modulos.clientes.bo import ClienteBO


def test_alta_email_duplicado() -> None:
    with pytest.raises(ReglaDeNegocioViolada, match="Ya existe un cliente"):
        ClienteBO().validar_alta(email_ya_registrado=True)


def test_baja_ya_inactivo() -> None:
    with pytest.raises(ReglaDeNegocioViolada, match="ya está inactivo"):
        ClienteBO().validar_baja(activo=False)


def test_cuit_invalido() -> None:
    with pytest.raises(ReglaDeNegocioViolada, match="CUIT"):
        ClienteBO().validar_datos_comerciales(
            "123", "consumidor_final", 0.0
        )


def test_datos_ok() -> None:
    ClienteBO().validar_datos_comerciales(
        "20-12345678-9", "responsable_inscripto", 1000.0
    )


def test_vendedor_inexistente() -> None:
    with pytest.raises(ReglaDeNegocioViolada, match="vendedor"):
        ClienteBO().validar_vendedor("x", False)
