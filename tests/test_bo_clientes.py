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


def test_baja_activo_ok() -> None:
    ClienteBO().validar_baja(activo=True)
