"""Tests unitarios de reglas fiscales ARCA/WSFE."""

import pytest

from app.core.excepciones import ReglaDeNegocioViolada
from app.modulos.ventas.fiscal import (
    armar_identidad,
    armar_qr,
    determinar_letra,
    documentacion_receptor,
    id_alicuota,
    validar_emision_fiscal,
)


def test_letra_ri_a_ri_es_a() -> None:
    assert determinar_letra("responsable_inscripto", "responsable_inscripto") == "A"


def test_letra_ri_a_cf_es_b() -> None:
    assert determinar_letra("responsable_inscripto", "consumidor_final") == "B"
    assert determinar_letra("responsable_inscripto", "monotributo") == "B"
    assert determinar_letra("responsable_inscripto", "exento") == "B"


def test_letra_monotributo_es_c() -> None:
    assert determinar_letra("monotributo", "responsable_inscripto") == "C"
    assert determinar_letra("exento", "consumidor_final") == "C"


def test_doc_con_cuit_es_80() -> None:
    tipo, nro = documentacion_receptor("responsable_inscripto", "20-12345678-6")
    assert tipo == 80
    assert nro == "20123456786"


def test_doc_cf_sin_cuit_es_99() -> None:
    tipo, nro = documentacion_receptor("consumidor_final", "")
    assert tipo == 99
    assert nro == "0"


def test_factura_a_requiere_cuit() -> None:
    with pytest.raises(ReglaDeNegocioViolada, match="Factura A"):
        validar_emision_fiscal(
            habilitada=True,
            cuit_emisor="30712345682",
            punto_venta=1,
            letra="A",
            doc_tipo=99,
            doc_nro="0",
        )


def test_sin_arca_no_valida() -> None:
    validar_emision_fiscal(
        habilitada=False,
        cuit_emisor="",
        punto_venta=0,
        letra="A",
        doc_tipo=99,
        doc_nro="0",
    )


def test_identidad_cf_factura_b() -> None:
    ident = armar_identidad(
        habilitada=True,
        cuit_emisor="30712345682",
        emisor_iva="responsable_inscripto",
        punto_venta=1,
        receptor_iva="consumidor_final",
        cuit_receptor="",
        iva_porcentaje=21.0,
    )
    assert ident.letra == "B"
    assert ident.cbte_tipo == 6
    assert ident.doc_tipo == 99
    assert ident.condicion_iva_receptor == 5


def test_identidad_c_anula_iva() -> None:
    ident = armar_identidad(
        habilitada=True,
        cuit_emisor="20111111112",
        emisor_iva="monotributo",
        punto_venta=1,
        receptor_iva="consumidor_final",
        cuit_receptor="",
        iva_porcentaje=21.0,
    )
    assert ident.letra == "C"
    assert ident.iva_porcentaje == 0.0


def test_alicuota_21() -> None:
    assert id_alicuota(21.0) == 5


def test_qr_contiene_cae() -> None:
    from datetime import date

    url = armar_qr(
        fecha=date(2026, 8, 29),
        cuit_emisor="30712345682",
        punto_venta=1,
        cbte_tipo=6,
        cbte_nro=12,
        importe=121.0,
        doc_tipo=99,
        doc_nro="0",
        cae="12345678901234",
    )
    assert url.startswith("https://www.afip.gob.ar/fe/qr/?p=")
