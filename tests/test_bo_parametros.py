"""Tests BO parámetros."""

import pytest

from app.core.excepciones import ReglaDeNegocioViolada
from app.modulos.parametros.bo import ParametrosBO


def test_formatear_numero_con_prefijo() -> None:
    assert ParametrosBO.formatear_numero("R-", 12) == "R-00000012"


def test_talonario_tipo_invalido() -> None:
    with pytest.raises(ReglaDeNegocioViolada, match="inválido"):
        ParametrosBO().validar_talonario("nota", 1)


def test_afip_requiere_cuit_si_habilita() -> None:
    with pytest.raises(ReglaDeNegocioViolada, match="CUIT"):
        ParametrosBO().validar_afip(
            habilitada=True,
            cuit="",
            condicion_iva="responsable_inscripto",
            punto_venta=1,
        )


def test_afip_limpia_cuit() -> None:
    cuit = ParametrosBO().validar_afip(
        habilitada=True,
        cuit="30-71234568-2",
        condicion_iva="responsable_inscripto",
        punto_venta=1,
    )
    assert cuit == "30712345682"
