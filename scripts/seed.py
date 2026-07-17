"""Seed mínimo de datos de demo.

Se ejecuta automáticamente al iniciar la API en dev (si la base está vacía)
o manualmente con:
    poetry run python -m scripts.seed

Si el esquema cambió (Fase A), borrá `data/ventas360.db` y volvé a sembrar.
"""

import asyncio
from datetime import date

from app.core.database import crear_tablas, fabrica_sesiones
from app.core.seguridad import hashear_password
from app.modulos.auth.dao import UsuarioDAO
from app.modulos.auth.models import Usuario
from app.modulos.bancos.models import CuentaBancaria
from app.modulos.clientes.models import Cliente
from app.modulos.parametros.models import Parametro, Talonario
from app.modulos.precios.models import ListaPrecio
from app.modulos.productos.models import Producto
from app.modulos.proveedores.models import Proveedor
from app.modulos.stock.models import Deposito, SaldoStock
from app.modulos.ventas.models import LineaPedido, Pedido
from app.modulos.zonas.models import Zona

EMAIL_DEMO = "admin@ventas360.com"
PASSWORD_DEMO = "demo12345"


async def _asegurar_zonas_demo(sesion) -> None:
    """Catálogo de zonas aunque el seed principal ya haya corrido."""
    existente = await sesion.get(Zona, "zona-1")
    if existente is not None:
        return
    sesion.add_all(
        [
            Zona(id="zona-1", nombre="Centro", codigo="CENTRO"),
            Zona(id="zona-2", nombre="Norte", codigo="NORTE"),
            Zona(id="zona-3", nombre="Rural", codigo="RURAL"),
        ]
    )
    await sesion.commit()


async def _asegurar_proveedores_demo(sesion) -> None:
    """Fase B1: proveedores demo aunque el seed principal ya haya corrido."""
    existente = await sesion.get(Proveedor, "prov-1")
    if existente is not None:
        return
    sesion.add_all(
        [
            Proveedor(
                id="prov-1",
                nombre="Distribuidora Andina SA",
                email="compras@andina.demo",
                telefono="11-4000-1001",
                cuit="30711222334",
                condicion_iva="responsable_inscripto",
            ),
            Proveedor(
                id="prov-2",
                nombre="Importadora Sur",
                email="ventas@importsur.demo",
                telefono="11-4000-1002",
                cuit="30799888776",
                condicion_iva="responsable_inscripto",
            ),
        ]
    )
    await sesion.commit()


async def _asegurar_tesoreria_demo(sesion) -> None:
    """Fase B2/B3: cuenta bancaria default si falta."""
    existente = await sesion.get(CuentaBancaria, "bco-1")
    if existente is not None:
        return
    sesion.add(
        CuentaBancaria(
            id="bco-1",
            codigo="CAJA-AHORRO",
            nombre="Caja de ahorro principal",
            banco="Banco Demo",
            cbu="0170000000000000000001",
            es_default=True,
        )
    )
    await sesion.commit()


async def sembrar_datos_demo() -> None:
    """Inserta admin, catálogos, stock, precios y pedidos de demo."""
    from scripts.seed_casuistica import (
        asegurar_casuistica_mostrador,
        asegurar_casuistica_rica,
        asegurar_cxc_remitos_emitidos,
    )

    async with fabrica_sesiones() as sesion:
        dao = UsuarioDAO(sesion)
        if await dao.buscar_por_email(EMAIL_DEMO) is not None:
            await _asegurar_zonas_demo(sesion)
            await _asegurar_proveedores_demo(sesion)
            await _asegurar_tesoreria_demo(sesion)
            cargada = await asegurar_casuistica_rica(sesion)
            if cargada:
                print("Casuística rica cargada sobre base existente.")
            mostrador = await asegurar_casuistica_mostrador(sesion)
            if mostrador:
                print("Casuística mostrador: ≥50 clientes + remitos + cta. cte.")
            n_cxc = await asegurar_cxc_remitos_emitidos(sesion)
            if n_cxc:
                print(f"CxC alineada con remitos emitidos ({n_cxc} movimientos).")
            return

        password_hash = hashear_password(PASSWORD_DEMO)
        admin = Usuario(
            nombre="Admin Demo",
            dni="20111222",
            email=EMAIL_DEMO,
            password_hash=password_hash,
            rol="administrador",
        )
        vendedor = Usuario(
            id="usr-vendedor-1",
            nombre="Vendedor Demo",
            dni="30123456",
            email="vendedor@ventas360.com",
            password_hash=password_hash,
            rol="vendedor",
        )
        sesion.add_all([admin, vendedor])
        await sesion.flush()

        zonas = [
            Zona(id="zona-1", nombre="Centro", codigo="CENTRO"),
            Zona(id="zona-2", nombre="Norte", codigo="NORTE"),
            Zona(id="zona-3", nombre="Rural", codigo="RURAL"),
        ]
        sesion.add_all(zonas)

        clientes = [
            Cliente(
                id="cli-1",
                nombre="María López",
                email="maria.lopez@email.com",
                telefono="+54 11 5555-1001",
                cuit="27333444556",
                condicion_iva="monotributo",
                limite_credito=500000.0,
                zona_id="zona-1",
                vendedor_id="usr-vendedor-1",
            ),
            Cliente(
                id="cli-2",
                nombre="Comercio San Martín",
                email="contacto@sanmartin.com.ar",
                telefono="+54 341 555-2200",
                cuit="30712345678",
                condicion_iva="responsable_inscripto",
                limite_credito=2000000.0,
                zona_id="zona-2",
                vendedor_id="usr-vendedor-1",
            ),
            Cliente(
                id="cli-3",
                nombre="Distribuidora Norte",
                email="ventas@norte.com.ar",
                telefono="+54 11 5555-3300",
                cuit="30111222334",
                condicion_iva="responsable_inscripto",
                limite_credito=5000000.0,
                zona_id="zona-3",
                observaciones="Cliente mayorista",
            ),
        ]
        sesion.add_all(clientes)

        productos = [
            Producto(
                id="prod-1",
                sku="NB-001",
                nombre='Notebook 14"',
                marca="TechBrand",
                rubro="Informática",
                codigo_barras="7790001000001",
                costo=650000.0,
                precio=850000.0,
                stock=12,
            ),
            Producto(
                id="prod-2",
                sku="MS-010",
                nombre="Mouse inalámbrico",
                marca="Logi",
                rubro="Periféricos",
                codigo_barras="7790001000002",
                costo=9000.0,
                precio=18500.0,
                stock=45,
            ),
            Producto(
                id="prod-3",
                sku="TK-200",
                nombre="Teclado mecánico",
                marca="KeyPro",
                rubro="Periféricos",
                codigo_barras="7790001000003",
                costo=22000.0,
                precio=42000.0,
                stock=20,
            ),
            Producto(
                id="prod-4",
                sku="MN-027",
                nombre='Monitor 27"',
                marca="ViewMax",
                rubro="Informática",
                codigo_barras="7790001000004",
                costo=210000.0,
                precio=320000.0,
                stock=8,
            ),
        ]
        # Catálogo extra para probar paginación/búsqueda.
        for i in range(5, 55):
            productos.append(
                Producto(
                    id=f"prod-{i}",
                    sku=f"ART-{i:04d}",
                    nombre=f"Artículo demo {i}",
                    marca="Genérica",
                    rubro="Varios",
                    codigo_barras=f"7790001{i:06d}",
                    costo=1000.0 * i,
                    precio=1500.0 * i,
                    stock=10 + i,
                )
            )
        sesion.add_all(productos)

        deposito = Deposito(id="dep-1", codigo="CENTRAL", nombre="Depósito central")
        sesion.add(deposito)
        lista = ListaPrecio(
            id="lista-1",
            codigo="GENERAL",
            nombre="Lista general",
            es_default=True,
        )
        sesion.add(lista)
        sesion.add_all(
            [
                Parametro(clave="iva_porcentaje", valor="21.0"),
                Parametro(clave="moneda", valor="ARS"),
                Parametro(clave="sucursal_codigo", valor="CENTRAL"),
                Parametro(clave="sucursal_nombre", valor="Casa central"),
                Parametro(clave="condiciones_pago", valor="contado,30_dias,60_dias"),
                Talonario(
                    id="tal-pedido",
                    tipo_comprobante="pedido",
                    prefijo="P-",
                    proximo_numero=1,
                ),
                Talonario(
                    id="tal-remito",
                    tipo_comprobante="remito",
                    prefijo="R-",
                    proximo_numero=1,
                ),
                Talonario(
                    id="tal-factura",
                    tipo_comprobante="factura",
                    prefijo="F-",
                    proximo_numero=1,
                ),
            ]
        )
        await sesion.flush()

        for p in productos:
            sesion.add(
                SaldoStock(
                    articulo_id=p.id,
                    deposito_id="dep-1",
                    cantidad=p.stock,
                )
            )

        pedido1 = Pedido(
            id="ped-1",
            tipo="pedido",
            cliente_id="cli-1",
            estado="confirmado",
            fecha=date.today(),
            neto=868500.0,
            iva=182385.0,
            iva_porcentaje=21.0,
            total=1050885.0,
            lineas=[
                LineaPedido(
                    producto_id="prod-1",
                    descripcion='Notebook 14"',
                    cantidad=1,
                    precio_unitario=850000.0,
                ),
                LineaPedido(
                    producto_id="prod-2",
                    descripcion="Mouse inalámbrico",
                    cantidad=1,
                    precio_unitario=18500.0,
                ),
            ],
        )
        pedido2 = Pedido(
            id="ped-2",
            tipo="pedido",
            cliente_id="cli-2",
            estado="entregado",
            fecha=date.today(),
            neto=362000.0,
            iva=76020.0,
            iva_porcentaje=21.0,
            total=438020.0,
            lineas=[
                LineaPedido(
                    producto_id="prod-4",
                    descripcion='Monitor 27"',
                    cantidad=1,
                    precio_unitario=320000.0,
                ),
                LineaPedido(
                    producto_id="prod-3",
                    descripcion="Teclado mecánico",
                    cantidad=1,
                    precio_unitario=42000.0,
                ),
            ],
        )
        remito_demo = Pedido(
            id="rem-1",
            tipo="remito",
            cliente_id="cli-3",
            deposito_id="dep-1",
            estado="borrador",
            fecha=date.today(),
            neto=42000.0,
            iva=8820.0,
            iva_porcentaje=21.0,
            total=50820.0,
            lineas=[
                LineaPedido(
                    producto_id="prod-3",
                    descripcion="Teclado mecánico",
                    cantidad=1,
                    precio_unitario=42000.0,
                ),
            ],
        )
        sesion.add_all([pedido1, pedido2, remito_demo])
        sesion.add_all(
            [
                Proveedor(
                    id="prov-1",
                    nombre="Distribuidora Andina SA",
                    email="compras@andina.demo",
                    telefono="11-4000-1001",
                    cuit="30711222334",
                    condicion_iva="responsable_inscripto",
                ),
                Proveedor(
                    id="prov-2",
                    nombre="Importadora Sur",
                    email="ventas@importsur.demo",
                    telefono="11-4000-1002",
                    cuit="30799888776",
                    condicion_iva="responsable_inscripto",
                ),
                CuentaBancaria(
                    id="bco-1",
                    codigo="CAJA-AHORRO",
                    nombre="Caja de ahorro principal",
                    banco="Banco Demo",
                    cbu="0170000000000000000001",
                    es_default=True,
                ),
            ]
        )

        await sesion.commit()
        await asegurar_casuistica_rica(sesion)
        await asegurar_casuistica_mostrador(sesion)
        await asegurar_cxc_remitos_emitidos(sesion)


if __name__ == "__main__":
    async def _main() -> None:
        await crear_tablas()
        await sembrar_datos_demo()
        print(f"Seed listo. Login demo: {EMAIL_DEMO} / {PASSWORD_DEMO}")
        print("Casuística: clientes, productos, comprobantes, compras, cta. cte.,")
        print("mostrador (≥50 clientes con remitos ≥5 ítems y saldos debe/a favor).")
        print("CxC: remitos confirmados/facturados imputan debe.")

    asyncio.run(_main())
