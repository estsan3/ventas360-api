"""BO del módulo cobranzas."""

from app.core.excepciones import ReglaDeNegocioViolada

MEDIOS = {"efectivo", "transferencia", "tarjeta"}


class CobranzasBO:
    def validar_medio(self, medio: str) -> None:
        if medio not in MEDIOS:
            raise ReglaDeNegocioViolada(f"Medio de cobro inválido: {medio}")

    def validar_recibo(self, monto: float, imputaciones: list[float]) -> None:
        if monto <= 0:
            raise ReglaDeNegocioViolada("El monto del recibo debe ser mayor a cero")
        if not imputaciones:
            raise ReglaDeNegocioViolada("El recibo debe imputar al menos una factura")
        if any(m <= 0 for m in imputaciones):
            raise ReglaDeNegocioViolada("Cada imputación debe ser mayor a cero")
        suma = round(sum(imputaciones), 2)
        if suma != round(monto, 2):
            raise ReglaDeNegocioViolada(
                f"La suma de imputaciones ({suma}) debe igualar el monto del recibo ({monto})"
            )
