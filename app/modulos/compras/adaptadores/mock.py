"""Parser mock para desarrollo y tests sin API key de Anthropic."""

from app.modulos.compras.puerto import LineaRemitoExtraida, PuertoParserRemitoVision, RemitoExtraido


class ParserRemitoMock(PuertoParserRemitoVision):
    """Devuelve líneas de demo alineadas al seed (periféricos / informática)."""

    async def parsear(self, contenido: bytes, media_type: str) -> RemitoExtraido:
        _ = contenido, media_type
        return RemitoExtraido(
            numero="REM-MOCK-001",
            fecha="2026-08-26",
            proveedor_texto="Proveedor demo",
            confianza=0.75,
            notas=["Modo mock: configurá VENTAS360_ANTHROPIC_API_KEY para usar Haiku."],
            lineas=[
                LineaRemitoExtraida(
                    descripcion="Mouse inalámbrico",
                    cantidad=10,
                    sku="MS-010",
                    codigo_barras="7790001000002",
                    precio_unitario=9000.0,
                ),
                LineaRemitoExtraida(
                    descripcion="Teclado mecánico",
                    cantidad=5,
                    sku="TK-200",
                    codigo_barras="7790001000003",
                    precio_unitario=22000.0,
                ),
            ],
        )
