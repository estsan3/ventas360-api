"""Parseo de tickets WSAA y respuestas WSFE (sin red)."""

from app.modulos.ventas.adaptadores.afip import parsear_cae
from app.modulos.ventas.adaptadores.wsaa import parsear_ticket


def test_parsear_ticket_wsaa_escapado() -> None:
    crudo = (
        "&lt;?xml version=&quot;1.0&quot; encoding=&quot;UTF-8&quot; "
        "standalone=&quot;yes&quot;?&gt;"
        "&lt;loginTicketResponse version=&quot;1.0&quot;&gt;"
        "&lt;header&gt;"
        "&lt;expirationTime&gt;2027-08-20T23:00:00-03:00&lt;/expirationTime&gt;"
        "&lt;/header&gt;"
        "&lt;credentials&gt;"
        "&lt;token&gt;TOKEN-DEMO&lt;/token&gt;"
        "&lt;sign&gt;SIGN-DEMO&lt;/sign&gt;"
        "&lt;/credentials&gt;"
        "&lt;/loginTicketResponse&gt;"
    )
    ticket = parsear_ticket(crudo)
    assert ticket.token == "TOKEN-DEMO"
    assert ticket.sign == "SIGN-DEMO"
    assert ticket.vigente()


def test_parsear_cae_ok() -> None:
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
      <soap:Body>
        <FECAESolicitarResponse xmlns="http://ar.gov.afip.dif.FEV1/">
          <FECAESolicitarResult>
            <FeCabResp><Resultado>A</Resultado></FeCabResp>
            <FeDetResp>
              <FECAEDetResponse>
                <CAE>70417054267475</CAE>
                <CAEFchVto>20260831</CAEFchVto>
                <Resultado>A</Resultado>
              </FECAEDetResponse>
            </FeDetResp>
          </FECAESolicitarResult>
        </FECAESolicitarResponse>
      </soap:Body>
    </soap:Envelope>
    """
    resultado = parsear_cae(xml, 12)
    assert resultado.autorizada is True
    assert resultado.cae == "70417054267475"
    assert resultado.cae_vencimiento is not None
    assert resultado.cae_vencimiento.isoformat() == "2026-08-31"


def test_parsear_cae_rechazado() -> None:
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
      <soap:Body>
        <FECAESolicitarResponse xmlns="http://ar.gov.afip.dif.FEV1/">
          <FECAESolicitarResult>
            <FeCabResp><Resultado>R</Resultado></FeCabResp>
            <Errors>
              <Err><Code>10016</Code><Msg>El numero de comprobante no es correlativo</Msg></Err>
            </Errors>
          </FECAESolicitarResult>
        </FECAESolicitarResponse>
      </soap:Body>
    </soap:Envelope>
    """
    resultado = parsear_cae(xml, 1)
    assert resultado.autorizada is False
    assert "correlativo" in resultado.error
