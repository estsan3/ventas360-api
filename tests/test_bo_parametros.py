"""Tests BO parámetros."""

import pytest

from app.core.excepciones import ReglaDeNegocioViolada
from app.modulos.parametros.bo import ParametrosBO


def test_formatear_numero_con_prefijo() -> None:
    assert ParametrosBO.formatear_numero("R-", 12) == "R-00000012"


def test_talonario_tipo_invalido() -> None:
    with pytest.raises(ReglaDeNegocioViolada, match="inválido"):
        ParametrosBO().validar_talonario("nota", 1)
