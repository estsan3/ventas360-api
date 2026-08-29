"""BO del módulo pagos."""

from dataclasses import dataclass

from app.core.excepciones import ReglaDeNegocioViolada
from app.modulos.bancos.schemas import DatosChequeRequest

MEDIOS = {"efectivo", "transferencia", "cheque"}


@dataclass(frozen=True)
class LineaMedioPago:
    medio: str
    monto: float
    cheque_id: str
    cheque: DatosChequeRequest | None


class PagosBO:
    def validar_medio(self, medio: str) -> None:
        if medio not in MEDIOS:
            raise ReglaDeNegocioViolada(f"Medio de pago inválido: {medio}")

    def validar_cheque_linea(self, linea: LineaMedioPago) -> None:
        if linea.medio != "cheque":
            return
        if linea.cheque_id and linea.cheque is not None:
            raise ReglaDeNegocioViolada(
                "El cheque es de cartera o propio, no los dos a la vez"
            )
        if not linea.cheque_id and linea.cheque is None:
            raise ReglaDeNegocioViolada(
                "Para pagar con cheque elegí uno de cartera o emití uno propio"
            )

    def normalizar_medios(
        self,
        monto: float,
        medio: str,
        cheque_id: str | None,
        cheque: DatosChequeRequest | None,
        medios: list[LineaMedioPago] | None,
    ) -> list[LineaMedioPago]:
        if medios:
            return medios
        return [
            LineaMedioPago(
                medio=medio,
                monto=round(monto, 2),
                cheque_id=(cheque_id or "").strip(),
                cheque=cheque,
            )
        ]

    def validar_medios(self, monto: float, lineas: list[LineaMedioPago]) -> str:
        if not lineas:
            raise ReglaDeNegocioViolada("El pago debe tener al menos un medio")
        if any(linea.monto <= 0 for linea in lineas):
            raise ReglaDeNegocioViolada("Cada medio de pago debe ser mayor a cero")
        for linea in lineas:
            self.validar_medio(linea.medio)
            self.validar_cheque_linea(linea)
        suma = round(sum(linea.monto for linea in lineas), 2)
        if suma != round(monto, 2):
            raise ReglaDeNegocioViolada(
                f"La suma de medios ({suma}) debe igualar el monto del pago ({monto})"
            )
        if monto <= 0:
            raise ReglaDeNegocioViolada("El monto del pago debe ser mayor a cero")
        if len(lineas) == 1:
            return lineas[0].medio
        return "mixto"
