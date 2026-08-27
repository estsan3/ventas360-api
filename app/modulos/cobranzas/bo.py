"""BO del módulo cobranzas."""

from dataclasses import dataclass

from app.core.excepciones import ReglaDeNegocioViolada
from app.modulos.bancos.schemas import DatosChequeRequest

MEDIOS = {"efectivo", "transferencia", "tarjeta", "cheque"}
MAX_CHEQUES_POR_RECIBO = 3


@dataclass(frozen=True)
class LineaMedio:
    medio: str
    monto: float
    cheque: DatosChequeRequest | None


class CobranzasBO:
    def validar_medio(self, medio: str) -> None:
        if medio not in MEDIOS:
            raise ReglaDeNegocioViolada(f"Medio de cobro inválido: {medio}")

    def validar_cheque(self, medio: str, hay_cheque: bool) -> None:
        if medio == "cheque" and not hay_cheque:
            raise ReglaDeNegocioViolada("Completá los datos del cheque")

    def normalizar_medios(
        self,
        monto: float,
        medio: str,
        cheque: DatosChequeRequest | None,
        medios: list[LineaMedio] | None,
    ) -> list[LineaMedio]:
        if medios:
            return medios
        return [LineaMedio(medio=medio, monto=round(monto, 2), cheque=cheque)]

    def validar_medios(self, monto: float, lineas: list[LineaMedio]) -> str:
        """Valida líneas de cobro y devuelve el medio a persistir en el recibo."""
        if not lineas:
            raise ReglaDeNegocioViolada("El recibo debe tener al menos un medio de cobro")
        if any(l.monto <= 0 for l in lineas):
            raise ReglaDeNegocioViolada("Cada medio de cobro debe ser mayor a cero")
        for linea in lineas:
            self.validar_medio(linea.medio)
            self.validar_cheque(linea.medio, linea.cheque is not None)
        n_cheques = sum(1 for l in lineas if l.medio == "cheque")
        if n_cheques > MAX_CHEQUES_POR_RECIBO:
            raise ReglaDeNegocioViolada(
                f"Como máximo se pueden registrar {MAX_CHEQUES_POR_RECIBO} cheques por cobro"
            )
        suma = round(sum(l.monto for l in lineas), 2)
        if suma != round(monto, 2):
            raise ReglaDeNegocioViolada(
                f"La suma de medios ({suma}) debe igualar el monto del recibo ({monto})"
            )
        if len(lineas) == 1:
            return lineas[0].medio
        return "mixto"

    def validar_recibo(self, monto: float, imputaciones: list[float]) -> None:
        if monto <= 0:
            raise ReglaDeNegocioViolada("El monto del recibo debe ser mayor a cero")
        if any(m <= 0 for m in imputaciones):
            raise ReglaDeNegocioViolada("Cada imputación debe ser mayor a cero")
        suma = round(sum(imputaciones), 2)
        if suma > round(monto, 2):
            raise ReglaDeNegocioViolada(
                f"La suma de imputaciones ({suma}) no puede superar el monto del recibo ({monto})"
            )
