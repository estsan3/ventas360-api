"""Service del módulo proveedores."""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.excepciones import RecursoNoEncontrado, ReglaDeNegocioViolada
from app.modulos.productos.contrato import ContratoProductos, ProductosLocal
from app.modulos.proveedores.bo import ProveedorBO
from app.modulos.proveedores.dao import ProveedorDAO
from app.modulos.proveedores.excel import parsear_lista_excel
from app.modulos.proveedores.models import Proveedor, _mapeo_default
from app.modulos.proveedores.schemas import (
    ActualizarProveedorRequest,
    CrearProveedorRequest,
    ImportarListaResponse,
    MapeoColumna,
    ProveedorResponse,
    ProveedoresPaginaResponse,
)


class ProveedoresService:
    def __init__(
        self,
        sesion: AsyncSession,
        productos: ContratoProductos | None = None,
    ) -> None:
        self._sesion = sesion
        self._dao = ProveedorDAO(sesion)
        self._bo = ProveedorBO()
        self._productos = productos or ProductosLocal(sesion)

    async def listar(
        self,
        *,
        q: str | None = None,
        activo: bool | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> ProveedoresPaginaResponse:
        items, total = await self._dao.listar(
            q=q, activo=activo, page=page, page_size=page_size
        )
        return ProveedoresPaginaResponse(
            items=[self._a_response(p) for p in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def obtener(self, proveedor_id: str) -> ProveedorResponse:
        return self._a_response(await self._buscar_o_fallar(proveedor_id))

    async def crear(self, datos: CrearProveedorRequest) -> ProveedorResponse:
        self._bo.validar_datos(datos.cuit, datos.condicion_iva, datos.nombre)
        self._bo.validar_politica(datos.politica_precio_venta)
        mapeo_raw = (
            [m.model_dump() for m in datos.mapeo_excel]
            if datos.mapeo_excel is not None
            else _mapeo_default()
        )
        mapeo = self._bo.validar_mapeo(mapeo_raw)
        proveedor = Proveedor(
            nombre=datos.nombre.strip(),
            email=str(datos.email or ""),
            telefono=datos.telefono,
            cuit=datos.cuit.replace("-", "").strip(),
            condicion_iva=datos.condicion_iva,
            observaciones=datos.observaciones,
            mapeo_excel=mapeo,
            excel_fila_inicio=datos.excel_fila_inicio,
            politica_precio_venta=datos.politica_precio_venta,
            margen_venta_pct=datos.margen_venta_pct,
        )
        await self._dao.guardar(proveedor)
        await self._sesion.commit()
        return self._a_response(proveedor)

    async def actualizar(
        self, proveedor_id: str, datos: ActualizarProveedorRequest
    ) -> ProveedorResponse:
        proveedor = await self._buscar_o_fallar(proveedor_id)
        if datos.nombre is not None:
            proveedor.nombre = datos.nombre.strip()
        if datos.email is not None:
            proveedor.email = str(datos.email)
        if datos.telefono is not None:
            proveedor.telefono = datos.telefono
        if datos.cuit is not None:
            proveedor.cuit = datos.cuit.replace("-", "").strip()
        if datos.condicion_iva is not None:
            proveedor.condicion_iva = datos.condicion_iva
        if datos.observaciones is not None:
            proveedor.observaciones = datos.observaciones
        if datos.mapeo_excel is not None:
            proveedor.mapeo_excel = self._bo.validar_mapeo(
                [m.model_dump() for m in datos.mapeo_excel]
            )
        if datos.excel_fila_inicio is not None:
            proveedor.excel_fila_inicio = datos.excel_fila_inicio
        if datos.politica_precio_venta is not None:
            self._bo.validar_politica(datos.politica_precio_venta)
            proveedor.politica_precio_venta = datos.politica_precio_venta
        if datos.margen_venta_pct is not None:
            proveedor.margen_venta_pct = datos.margen_venta_pct
        self._bo.validar_datos(
            proveedor.cuit, proveedor.condicion_iva, proveedor.nombre
        )
        await self._dao.guardar(proveedor)
        await self._sesion.commit()
        return self._a_response(proveedor)

    async def desactivar(self, proveedor_id: str) -> ProveedorResponse:
        proveedor = await self._buscar_o_fallar(proveedor_id)
        self._bo.validar_baja(proveedor.activo)
        proveedor.activo = False
        await self._dao.guardar(proveedor)
        await self._sesion.commit()
        return self._a_response(proveedor)

    async def importar_lista(
        self,
        proveedor_id: str,
        *,
        contenido: bytes,
        nombre_archivo: str,
        mapeo_override: list[dict[str, str]] | None = None,
        fila_inicio: int | None = None,
        politica: str | None = None,
        margen_pct: float | None = None,
        dry_run: bool = False,
    ) -> ImportarListaResponse:
        proveedor = await self._buscar_o_fallar(proveedor_id)
        if not proveedor.activo:
            raise ReglaDeNegocioViolada("El proveedor está inactivo")

        mapeo_src = mapeo_override if mapeo_override is not None else list(proveedor.mapeo_excel or [])
        mapeo = self._bo.validar_mapeo(mapeo_src)
        fila = fila_inicio if fila_inicio is not None else proveedor.excel_fila_inicio
        pol = politica or proveedor.politica_precio_venta
        self._bo.validar_politica(pol)
        margen = margen_pct if margen_pct is not None else proveedor.margen_venta_pct

        parseado = parsear_lista_excel(contenido, mapeo, fila)
        actualizados = 0
        nuevos = 0
        sin_match_codigos: list[str] = []
        omitidas = list(parseado.omitidas)

        for fila_lista in parseado.filas:
            precio_venta, actualizar_precio = self._bo.resolver_precio_venta(
                politica=pol,
                costo=fila_lista.costo,
                precio_lista=fila_lista.precio_lista,
                margen_pct=margen,
            )
            existente = await self._productos.obtener_por_sku(fila_lista.sku)
            if existente is None and not fila_lista.nombre:
                sin_match_codigos.append(fila_lista.sku)
                continue
            if dry_run:
                if existente is None:
                    nuevos += 1
                else:
                    actualizados += 1
                continue
            try:
                _, accion = await self._productos.upsert_desde_lista(
                    sku=fila_lista.sku,
                    nombre=fila_lista.nombre,
                    costo=fila_lista.costo,
                    precio=precio_venta,
                    marca=fila_lista.marca,
                    rubro=fila_lista.rubro,
                    actualizar_precio_venta=actualizar_precio,
                )
            except ReglaDeNegocioViolada as exc:
                omitidas.append(f"SKU {fila_lista.sku}: {exc}")
                continue
            if accion == "creado":
                nuevos += 1
            else:
                actualizados += 1

        if not dry_run:
            if mapeo_override is not None:
                proveedor.mapeo_excel = mapeo
            if fila_inicio is not None:
                proveedor.excel_fila_inicio = fila
            if politica is not None:
                proveedor.politica_precio_venta = pol
            if margen_pct is not None:
                proveedor.margen_venta_pct = margen
            proveedor.ultima_importacion_fecha = datetime.now(timezone.utc).replace(tzinfo=None)
            proveedor.ultima_importacion_archivo = (nombre_archivo or "lista.xlsx")[:255]
            proveedor.ultima_importacion_actualizados = actualizados
            proveedor.ultima_importacion_nuevos = nuevos
            proveedor.ultima_importacion_sin_match = len(sin_match_codigos)
            await self._dao.guardar(proveedor)
            await self._sesion.commit()

        return ImportarListaResponse(
            proveedor_id=proveedor.id,
            archivo=nombre_archivo or "lista.xlsx",
            dry_run=dry_run,
            actualizados=actualizados,
            nuevos=nuevos,
            sin_match=len(sin_match_codigos),
            omitidas=omitidas[:50],
            sin_match_codigos=sin_match_codigos[:50],
            preview_cols=parseado.preview_cols,
            preview_rows=parseado.preview_rows,
        )

    async def _buscar_o_fallar(self, proveedor_id: str) -> Proveedor:
        proveedor = await self._dao.buscar_por_id(proveedor_id)
        if proveedor is None:
            raise RecursoNoEncontrado("Proveedor no encontrado")
        return proveedor

    def _a_response(self, proveedor: Proveedor) -> ProveedorResponse:
        mapeo_raw: list[Any] = list(proveedor.mapeo_excel or [])
        mapeo = [
            MapeoColumna(
                columna=str(item.get("columna", "")),
                campo=str(item.get("campo", "")),
            )
            for item in mapeo_raw
            if isinstance(item, dict)
        ]
        return ProveedorResponse(
            id=proveedor.id,
            nombre=proveedor.nombre,
            email=proveedor.email,
            telefono=proveedor.telefono,
            cuit=proveedor.cuit,
            condicion_iva=proveedor.condicion_iva,  # type: ignore[arg-type]
            observaciones=proveedor.observaciones,
            activo=proveedor.activo,
            mapeo_excel=mapeo,
            excel_fila_inicio=proveedor.excel_fila_inicio or 2,
            politica_precio_venta=proveedor.politica_precio_venta or "solo_costo",  # type: ignore[arg-type]
            margen_venta_pct=proveedor.margen_venta_pct or 30.0,
            ultima_importacion_fecha=proveedor.ultima_importacion_fecha,
            ultima_importacion_archivo=proveedor.ultima_importacion_archivo or "",
            ultima_importacion_actualizados=proveedor.ultima_importacion_actualizados or 0,
            ultima_importacion_nuevos=proveedor.ultima_importacion_nuevos or 0,
            ultima_importacion_sin_match=proveedor.ultima_importacion_sin_match or 0,
        )
