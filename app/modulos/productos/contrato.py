"""Contrato público del módulo productos."""

from dataclasses import dataclass
from typing import Literal, Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.excepciones import ReglaDeNegocioViolada
from app.modulos.productos.bo import ProductoBO
from app.modulos.productos.dao import ProductoDAO
from app.modulos.productos.models import Producto


@dataclass(frozen=True)
class ProductoResumen:
    """Datos mínimos de un producto para otros módulos."""

    id: str
    sku: str
    nombre: str
    precio: float
    costo: float
    stock: int
    activo: bool


class ContratoProductos(Protocol):
    """Interfaz que productos garantiza al resto del sistema."""

    async def contar_activos(self) -> int: ...

    async def stock_total(self) -> int: ...

    async def obtener_producto(self, producto_id: str) -> ProductoResumen | None: ...

    async def obtener_por_sku(self, sku: str) -> ProductoResumen | None: ...

    async def listar_activos(self) -> list[ProductoResumen]: ...

    async def upsert_desde_lista(
        self,
        *,
        sku: str,
        nombre: str,
        costo: float,
        precio: float | None = None,
        marca: str = "",
        rubro: str = "",
        actualizar_precio_venta: bool = False,
    ) -> tuple[ProductoResumen, Literal["creado", "actualizado"]]: ...


class ProductosLocal:
    """Implementación local del contrato (mismo proceso, misma base)."""

    def __init__(self, sesion: AsyncSession) -> None:
        self._dao = ProductoDAO(sesion)
        self._bo = ProductoBO()

    async def contar_activos(self) -> int:
        return await self._dao.contar_activos()

    async def stock_total(self) -> int:
        return await self._dao.stock_total()

    async def obtener_producto(self, producto_id: str) -> ProductoResumen | None:
        producto = await self._dao.buscar_por_id(producto_id)
        return self._a_resumen(producto) if producto else None

    async def obtener_por_sku(self, sku: str) -> ProductoResumen | None:
        producto = await self._dao.buscar_por_sku(sku.strip())
        return self._a_resumen(producto) if producto else None

    async def listar_activos(self) -> list[ProductoResumen]:
        return [self._a_resumen(p) for p in await self._dao.listar_activos()]

    async def upsert_desde_lista(
        self,
        *,
        sku: str,
        nombre: str,
        costo: float,
        precio: float | None = None,
        marca: str = "",
        rubro: str = "",
        actualizar_precio_venta: bool = False,
    ) -> tuple[ProductoResumen, Literal["creado", "actualizado"]]:
        """Crea o actualiza un artículo desde la lista del proveedor.

        Sin commit: lo controla el service orquestador.
        """
        sku_limpio = sku.strip()
        existente = await self._dao.buscar_por_sku(sku_limpio)
        if existente is None:
            if not nombre.strip():
                raise ReglaDeNegocioViolada(
                    "Artículo nuevo requiere descripción en la lista"
                )
            precio_final = precio if precio is not None and precio > 0 else max(costo, 0.01)
            self._bo.validar_precios(costo, precio_final)
            producto = Producto(
                sku=sku_limpio[:40],
                nombre=nombre.strip()[:120],
                marca=(marca or "")[:80],
                rubro=(rubro or "")[:80],
                costo=costo,
                precio=precio_final,
                stock=0,
            )
            await self._dao.guardar(producto)
            return self._a_resumen(producto), "creado"

        existente.costo = costo
        if nombre.strip():
            existente.nombre = nombre.strip()[:120]
        if marca:
            existente.marca = marca[:80]
        if rubro:
            existente.rubro = rubro[:80]
        if actualizar_precio_venta and precio is not None and precio > 0:
            existente.precio = precio
        self._bo.validar_precios(existente.costo, existente.precio)
        await self._dao.guardar(existente)
        return self._a_resumen(existente), "actualizado"

    def _a_resumen(self, producto: Producto) -> ProductoResumen:
        return ProductoResumen(
            id=producto.id,
            sku=producto.sku,
            nombre=producto.nombre,
            precio=producto.precio,
            costo=producto.costo,
            stock=producto.stock,
            activo=producto.activo,
        )
