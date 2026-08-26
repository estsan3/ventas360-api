"""BO del módulo caja."""

from app.core.excepciones import ReglaDeNegocioViolada

TIPOS = {"ingreso", "egreso"}
MEDIOS = {"efectivo", "tarjeta", "cheque", "otro"}


class CajaBO:
    def validar_movimiento(self, tipo: str, medio: str, monto: float) -> None:
        if tipo not in TIPOS:
            raise ReglaDeNegocioViolada(f"Tipo de caja inválido: {tipo}")
        if medio not in MEDIOS:
            raise ReglaDeNegocioViolada(f"Medio de caja inválido: {medio}")
        if monto <= 0:
            raise ReglaDeNegocioViolada("El monto debe ser mayor a cero")

    def validar_fondo(self, fondo: float) -> None:
        if fondo < 0:
            raise ReglaDeNegocioViolada("El fondo inicial no puede ser negativo")

    def validar_contado(self, contado: float, etiqueta: str = "contado") -> None:
        if contado < 0:
            raise ReglaDeNegocioViolada(f"El {etiqueta} no puede ser negativo")

    def validar_apertura(self, sesion_abierta: object | None) -> None:
        if sesion_abierta is not None:
            raise ReglaDeNegocioViolada("Ya hay una caja abierta")

    def validar_caja_abierta(self, sesion: object | None) -> None:
        if sesion is None or getattr(sesion, "estado", "") != "abierta":
            raise ReglaDeNegocioViolada("La caja no está abierta")

    def validar_egreso_efectivo(self, monto: float, efectivo_esperado: float) -> None:
        if round(monto, 2) > round(efectivo_esperado, 2):
            raise ReglaDeNegocioViolada("No hay suficiente efectivo en caja")

    def validar_datos_cheque(self, tipo: str, cheque_id: str | None, hay_cheque: bool) -> None:
        if tipo == "ingreso" and not hay_cheque:
            raise ReglaDeNegocioViolada("Completá los datos del cheque recibido")
        if tipo == "egreso" and not cheque_id and not hay_cheque:
            raise ReglaDeNegocioViolada(
                "Elegí un cheque de cartera o emití uno propio"
            )

    def validar_monto_cheque(self, monto: float, valor_monto: float) -> None:
        if round(monto, 2) != round(valor_monto, 2):
            raise ReglaDeNegocioViolada("El monto debe coincidir con el del cheque")

    def validar_concepto_egreso(self, concepto: str) -> None:
        if len((concepto or "").strip()) < 3:
            raise ReglaDeNegocioViolada("El egreso necesita un concepto")

    @staticmethod
    def calcular_saldo(ingresos: float, egresos: float) -> float:
        return round(ingresos - egresos, 2)

    @staticmethod
    def calcular_diferencia(esperado: float, contado: float) -> float:
        return round(contado - esperado, 2)
