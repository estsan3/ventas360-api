"""Casuística amplia de demo para probar todas las pantallas.

Idempotente: si ya existe el marcador `cli-delta`, no vuelve a insertar.
Se invoca desde `scripts.seed.sembrar_datos_demo`.
"""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.modulos.auth.models import Usuario
from app.modulos.bancos.models import CuentaBancaria, MovimientoBancario, ValorBancario
from app.modulos.caja.models import MovimientoCaja
from app.modulos.clientes.models import Cliente
from app.modulos.compras.models import Compra, LineaCompra
from app.modulos.cxc.models import MovimientoCxc
from app.modulos.cxp.models import MovimientoCxp
from app.modulos.parametros.models import Talonario
from app.modulos.precios.models import ListaPrecio, PrecioArticulo
from app.modulos.productos.models import Producto
from app.modulos.proveedores.models import Proveedor
from app.modulos.stock.models import Deposito, MovimientoStock, SaldoStock
from app.modulos.ventas.models import LineaPedido, Pedido
from app.modulos.zonas.models import Zona

HOY = date.today()
IVA = 21.0


def _imp(neto: float) -> tuple[float, float, float]:
    iva = round(neto * IVA / 100, 2)
    return neto, iva, round(neto + iva, 2)


def _linea(producto_id: str, descripcion: str, cantidad: int, precio: float) -> LineaPedido:
    return LineaPedido(
        producto_id=producto_id,
        descripcion=descripcion,
        cantidad=cantidad,
        precio_unitario=precio,
    )


def _linea_c(producto_id: str, descripcion: str, cantidad: int, precio: float) -> LineaCompra:
    return LineaCompra(
        producto_id=producto_id,
        descripcion=descripcion,
        cantidad=cantidad,
        precio_unitario=precio,
    )


async def asegurar_casuistica_rica(sesion: AsyncSession) -> bool:
    """Carga casuística rica. Devuelve True si insertó datos nuevos."""
    if await sesion.get(Cliente, "cli-delta") is not None:
        return False

    # --- Usuarios extra ---
    if await sesion.get(Usuario, "usr-vendedor-2") is None:
        from app.core.seguridad import hashear_password

        pwd = hashear_password("demo12345")
        sesion.add_all(
            [
                Usuario(
                    id="usr-vendedor-2",
                    nombre="Laura Paredes",
                    dni="28990112",
                    email="lparedes@ventas360.com",
                    password_hash=pwd,
                    rol="vendedor",
                ),
                Usuario(
                    id="usr-contable-1",
                    nombre="Griselda Otaño",
                    dni="25111222",
                    email="gotano@ventas360.com",
                    password_hash=pwd,
                    rol="administrador",
                ),
            ]
        )

    # --- Zonas ---
    for zid, nombre, codigo in [
        ("zona-1", "Centro", "CENTRO"),
        ("zona-2", "Norte", "NORTE"),
        ("zona-3", "Rural", "RURAL"),
        ("zona-4", "Sur", "SUR"),
        ("zona-5", "Industrial", "IND"),
    ]:
        if await sesion.get(Zona, zid) is None:
            sesion.add(Zona(id=zid, nombre=nombre, codigo=codigo))

    # --- Depósitos ---
    for did, codigo, nombre in [
        ("dep-1", "CENTRAL", "Depósito Central"),
        ("dep-2", "ANEXO", "Depósito 2 — Anexo"),
        ("dep-3", "CORRALON", "Depósito 3 — Corralón"),
    ]:
        if await sesion.get(Deposito, did) is None:
            sesion.add(Deposito(id=did, codigo=codigo, nombre=nombre))

    # --- Listas de precio ---
    for lid, codigo, nombre, default in [
        ("lista-1", "GENERAL", "Lista 1 — Minorista", True),
        ("lista-2", "MAYOR", "Lista 2 — Mayorista", False),
        ("lista-3", "OBRA", "Lista 3 — Obra / constructor", False),
    ]:
        if await sesion.get(ListaPrecio, lid) is None:
            sesion.add(
                ListaPrecio(id=lid, codigo=codigo, nombre=nombre, es_default=default)
            )

    if await sesion.get(Talonario, "tal-presupuesto") is None:
        sesion.add(
            Talonario(
                id="tal-presupuesto",
                tipo_comprobante="presupuesto",
                prefijo="PRE-",
                proximo_numero=100,
            )
        )

    # --- Clientes (casuística CRM / cta cte / zonas / estados) ---
    clientes = [
        Cliente(
            id="cli-delta",
            nombre="Constructora Delta SRL",
            email="compras@deltasrl.com.ar",
            telefono="02302 42-7788",
            cuit="30708123459",
            condicion_iva="responsable_inscripto",
            limite_credito=500000.0,
            zona_id="zona-1",
            vendedor_id="usr-vendedor-1",
            observaciones="Delta Construcciones · Lista 2 · Cta. cte. 30 días",
        ),
        Cliente(
            id="cli-mitre",
            nombre="Corralón Mitre SA",
            email="admin@corralonmitre.com.ar",
            telefono="02302 43-1100",
            cuit="30654098213",
            condicion_iva="responsable_inscripto",
            limite_credito=300000.0,
            zona_id="zona-2",
            vendedor_id="usr-vendedor-1",
            bloqueado=True,
            observaciones="Bloqueado por mora — vencido $187.400",
        ),
        Cliente(
            id="cli-ceibo",
            nombre="Agropecuaria El Ceibo",
            email="compras@elceibo.com.ar",
            telefono="02302 49-2200",
            cuit="30712345671",
            condicion_iva="responsable_inscripto",
            limite_credito=800000.0,
            zona_id="zona-3",
            vendedor_id="usr-vendedor-2",
            observaciones="Entrega en establecimiento Metileo",
        ),
        Cliente(
            id="cli-anibal",
            nombre="Rodríguez, Aníbal",
            email="anibal.rodriguez@email.com",
            telefono="2302 55-8899",
            cuit="20284561237",
            condicion_iva="monotributo",
            limite_credito=80000.0,
            zona_id="zona-1",
            vendedor_id="usr-vendedor-1",
        ),
        Cliente(
            id="cli-pintado",
            nombre="Pintado Fácil (M. Suárez)",
            email="pintadofacil@gmail.com",
            telefono="2302 61-3344",
            cuit="27332189045",
            condicion_iva="monotributo",
            limite_credito=120000.0,
            zona_id="zona-2",
            vendedor_id="usr-vendedor-2",
        ),
        Cliente(
            id="cli-metal",
            nombre="Metalúrgica Pampa SRL",
            email="compras@metalpampa.com.ar",
            telefono="02302 45-6677",
            cuit="30698754122",
            condicion_iva="responsable_inscripto",
            limite_credito=1000000.0,
            zona_id="zona-5",
            vendedor_id="usr-vendedor-1",
            observaciones="Planta Ruta 1 km 4",
        ),
        Cliente(
            id="cli-cf",
            nombre="Consumidor Final",
            email="cf@ventas360.com",
            telefono="",
            cuit="",
            condicion_iva="consumidor_final",
            limite_credito=0.0,
            zona_id="zona-1",
        ),
        Cliente(
            id="cli-exento",
            nombre="Cooperativa Escolar Pico",
            email="coop@escolar.pico.edu.ar",
            telefono="02302 42-1000",
            cuit="30600111223",
            condicion_iva="exento",
            limite_credito=50000.0,
            zona_id="zona-1",
        ),
        Cliente(
            id="cli-inactivo",
            nombre="Ferretería Vieja SA",
            email="cerrada@vieja.demo",
            telefono="",
            cuit="30555444332",
            condicion_iva="responsable_inscripto",
            limite_credito=0.0,
            zona_id="zona-4",
            activo=False,
            observaciones="Baja comercial 2025",
        ),
        Cliente(
            id="cli-sinlimite",
            nombre="Obra Pública Municipal",
            email="compras@muni.pico.gov.ar",
            telefono="02302 42-0001",
            cuit="30666999888",
            condicion_iva="exento",
            limite_credito=0.0,
            zona_id="zona-1",
            observaciones="Sin límite formal — autorización por OC",
        ),
        Cliente(
            id="cli-speluzzi",
            nombre="Corralón Speluzzi Hnos",
            email="speluzzi@correo.com",
            telefono="02302 48-5511",
            cuit="30777888999",
            condicion_iva="responsable_inscripto",
            limite_credito=250000.0,
            zona_id="zona-2",
            vendedor_id="usr-vendedor-2",
        ),
        Cliente(
            id="cli-taller",
            nombre="Taller El Rápido",
            email="tallerelrapido@gmail.com",
            telefono="2302 66-1122",
            cuit="20333444556",
            condicion_iva="monotributo",
            limite_credito=40000.0,
            zona_id="zona-1",
            vendedor_id="usr-vendedor-1",
        ),
    ]
    sesion.add_all(clientes)

    # --- Productos ferretería / corralón (mock DC) ---
    catalogo = [
        ("prod-amo750", "AMO-750", "Amoladora angular 750W 115mm", "Bosch", "Herramientas", 61900, 89900, 12),
        ("prod-dis115", "DIS-115", "Disco de corte 115×1.6mm acero", "Tyrolit", "Herramientas", 1480, 2350, 0),
        ("prod-tor850", "TOR-850", "Tornillo fix 8×50 caja ×100", "Fischer", "Fijaciones", 5900, 9400, 4),
        ("prod-lat20b", "LAT-20B", "Látex interior blanco 20L", "Alba", "Pinturas", 48200, 72900, 28),
        ("prod-cab2x15", "CAB-2X15", "Cable taller 2×1.5mm rollo 100m", "Prysmian", "Electricidad", 38700, 58900, 7),
        ("prod-guan09", "GUA-N09", "Guante nitrilo T9 par", "Libus", "Seguridad", 2100, 3600, 0),
        ("prod-tal13", "TAL-13", "Taladro percutor 13mm 650W", "Black+Decker", "Herramientas", 52400, 78500, 9),
        ("prod-cinp24", "CIN-P24", "Cinta papel 24mm", "Doble A", "Pinturas", 890, 1450, 6),
        ("prod-coramk", "COR-AMK20", "Correa Poly-V VW Amarok 2.0 TDI", "Gates", "Correas", 24800, 38400, 6),
        ("prod-coramkd", "COR-AMKD", "Correa distribución VW Amarok 2.0 (kit)", "Continental", "Correas", 62000, 96200, 3),
        ("prod-tenamk", "TEN-AMK", "Tensor de correa VW Amarok", "SKF", "Correas", 34000, 52700, 1),
        ("prod-corv6", "COR-AMKV6", "Correa alternador VW Amarok V6", "Gates", "Correas", 29000, 44900, 0),
        ("prod-esm1l", "ESM-1L", "Esmalte sintético 1L", "Alba", "Pinturas", 6200, 9600, 40),
        ("prod-mem10", "MEM-10", "Membrana asfáltica 10m²", "Danosa", "Construcción", 18500, 28900, 86),
        ("prod-pishvlp", "PIS-HVLP", "Pistola pintar HVLP", "Devilbiss", "Pinturas", 42000, 68500, 14),
        ("prod-discooff", "DIS-OFF", "Disco corte descontinuado", "Genérica", "Herramientas", 500, 900, 0),
    ]
    productos_nuevos: list[Producto] = []
    for pid, sku, nombre, marca, rubro, costo, precio, stock in catalogo:
        if await sesion.get(Producto, pid) is None:
            p = Producto(
                id=pid,
                sku=sku,
                nombre=nombre,
                marca=marca,
                rubro=rubro,
                codigo_barras=f"779{abs(hash(sku)) % 10_000_000_000:010d}"[:13],
                costo=float(costo),
                precio=float(precio),
                stock=stock,
                activo=pid != "prod-discooff",
            )
            productos_nuevos.append(p)
            sesion.add(p)

    # Artículos genéricos extras para paginación/filtros
    for i in range(100, 140):
        pid = f"prod-extra-{i}"
        if await sesion.get(Producto, pid) is None:
            rubros = ["Herramientas", "Fijaciones", "Pinturas", "Electricidad", "Seguridad"]
            p = Producto(
                id=pid,
                sku=f"EXT-{i:04d}",
                nombre=f"Artículo casuística {i}",
                marca="Genérica",
                rubro=rubros[i % len(rubros)],
                codigo_barras=f"7799001{i:06d}",
                costo=500.0 * (i % 20 + 1),
                precio=800.0 * (i % 20 + 1),
                stock=(i % 15) * 3,
            )
            productos_nuevos.append(p)
            sesion.add(p)

    await sesion.flush()

    # Stock multi-depósito + casos bajo mínimo / sin stock
    for p in productos_nuevos:
        # Central
        sesion.add(
            SaldoStock(articulo_id=p.id, deposito_id="dep-1", cantidad=p.stock)
        )
        # Anexo: mitad o cero
        sesion.add(
            SaldoStock(
                articulo_id=p.id,
                deposito_id="dep-2",
                cantidad=max(0, p.stock // 3),
            )
        )
        # Corralón: poco
        sesion.add(
            SaldoStock(
                articulo_id=p.id,
                deposito_id="dep-3",
                cantidad=2 if p.stock > 10 else 0,
            )
        )

    # Precios en listas 2 y 3 (mayorista ~8% menos, obra ~12% menos)
    for p in productos_nuevos[:16]:
        sesion.add(
            PrecioArticulo(
                lista_id="lista-2", articulo_id=p.id, precio=round(p.precio * 0.92, 2)
            )
        )
        sesion.add(
            PrecioArticulo(
                lista_id="lista-3", articulo_id=p.id, precio=round(p.precio * 0.88, 2)
            )
        )

    # Movimientos de stock (ajustes / ingresos)
    sesion.add_all(
        [
            MovimientoStock(
                articulo_id="prod-amo750",
                deposito_id="dep-1",
                tipo="ajuste",
                cantidad=-1,
                referencia="INV-0042 dif",
            ),
            MovimientoStock(
                articulo_id="prod-lat20b",
                deposito_id="dep-1",
                tipo="ingreso",
                cantidad=10,
                referencia="RP recepción Herrafe",
            ),
            MovimientoStock(
                articulo_id="prod-dis115",
                deposito_id="dep-1",
                tipo="egreso_remito",
                cantidad=-12,
                referencia="REM venta",
            ),
        ]
    )

    # --- Proveedores ---
    proveedores = [
        Proveedor(
            id="prov-herrafe",
            nombre="Distribuidora Herrafe SA",
            email="j.almada@herrafe.com",
            telefono="011 4780-2200",
            cuit="30587123406",
            observaciones="Herramientas y fijaciones · 30 días FF",
        ),
        Proveedor(
            id="prov-pinturas",
            nombre="Pinturerías del Centro SRL",
            email="s.vega@pinturascentro.com",
            telefono="02954 43-1122",
            cuit="30642917852",
            observaciones="Pinturas · Contado 5% dto.",
        ),
        Proveedor(
            id="prov-electrica",
            nombre="Eléctrica Pampeana",
            email="r.funes@electricapampeana.com",
            telefono="02302 43-8890",
            cuit="30709988124",
            observaciones="Material eléctrico · 15 días FF",
        ),
        Proveedor(
            id="prov-inactivo",
            nombre="Proveedor Histórico SA",
            email="info@historico.demo",
            telefono="",
            cuit="30111000999",
            observaciones="Inactivo",
            activo=False,
        ),
    ]
    sesion.add_all(proveedores)

    # --- Comprobantes de venta ---
    def fac(
        id_: str,
        cliente: str,
        estado: str,
        dias: int,
        lineas: list[LineaPedido],
        numero: str | None = None,
        tipo: str = "factura",
        deposito: str | None = "dep-1",
        origen: str | None = None,
    ) -> Pedido:
        neto = sum(l.cantidad * l.precio_unitario for l in lineas)
        n, i, t = _imp(neto)
        return Pedido(
            id=id_,
            tipo=tipo,
            cliente_id=cliente,
            estado=estado,
            deposito_id=deposito if tipo in ("remito", "factura", "pedido") else None,
            origen_id=origen,
            fecha=HOY - timedelta(days=dias),
            neto=n,
            iva=i,
            iva_porcentaje=IVA,
            total=t,
            numero=numero,
            cae="12345678901234" if tipo == "factura" and estado == "confirmado" else None,
            lineas=lineas,
        )

    ventas = [
        # Presupuestos
        fac(
            "pre-vigente-1",
            "cli-delta",
            "vigente",
            2,
            [_linea("prod-amo750", "Amoladora angular 750W 115mm", 2, 89900)],
            "PRE-000100",
            "presupuesto",
            None,
        ),
        fac(
            "pre-aceptado-1",
            "cli-ceibo",
            "aceptado",
            5,
            [
                _linea("prod-lat20b", "Látex interior blanco 20L", 5, 72900),
                _linea("prod-esm1l", "Esmalte sintético 1L", 10, 9600),
            ],
            "PRE-000101",
            "presupuesto",
            None,
        ),
        fac(
            "pre-vencido-1",
            "cli-pintado",
            "vencido",
            40,
            [_linea("prod-cinp24", "Cinta papel 24mm", 20, 1450)],
            "PRE-000080",
            "presupuesto",
            None,
        ),
        fac(
            "pre-borrador-1",
            "cli-anibal",
            "borrador",
            0,
            [_linea("prod-tal13", "Taladro percutor 13mm 650W", 1, 78500)],
            None,
            "presupuesto",
            None,
        ),
        fac(
            "pre-convertido-1",
            "cli-metal",
            "convertido",
            15,
            [_linea("prod-cab2x15", "Cable taller 2×1.5mm rollo 100m", 3, 58900)],
            "PRE-000090",
            "presupuesto",
            None,
        ),
        fac(
            "pre-cancelado-1",
            "cli-taller",
            "cancelado",
            8,
            [_linea("prod-guan09", "Guante nitrilo T9 par", 10, 3600)],
            "PRE-000085",
            "presupuesto",
            None,
        ),
        # Pedidos
        fac(
            "ped-borr-1",
            "cli-delta",
            "borrador",
            0,
            [
                _linea("prod-tor850", "Tornillo fix 8×50 caja ×100", 5, 9400),
                _linea("prod-dis115", "Disco de corte 115×1.6mm acero", 20, 2350),
            ],
            "P-000401",
            "pedido",
        ),
        fac(
            "ped-conf-1",
            "cli-ceibo",
            "confirmado",
            1,
            [_linea("prod-lat20b", "Látex interior blanco 20L", 8, 72900)],
            "P-000402",
            "pedido",
        ),
        fac(
            "ped-conf-2",
            "cli-metal",
            "confirmado",
            3,
            [
                _linea("prod-amo750", "Amoladora angular 750W 115mm", 1, 89900),
                _linea("prod-guan09", "Guante nitrilo T9 par", 12, 3600),
            ],
            "P-000403",
            "pedido",
        ),
        fac(
            "ped-ent-1",
            "cli-pintado",
            "entregado",
            6,
            [_linea("prod-esm1l", "Esmalte sintético 1L", 6, 9600)],
            "P-000390",
            "pedido",
        ),
        fac(
            "ped-ent-2",
            "cli-anibal",
            "entregado",
            10,
            [_linea("prod-coramk", "Correa Poly-V VW Amarok 2.0 TDI", 1, 38400)],
            "P-000385",
            "pedido",
        ),
        fac(
            "ped-canc-1",
            "cli-speluzzi",
            "cancelado",
            12,
            [_linea("prod-mem10", "Membrana asfáltica 10m²", 2, 28900)],
            "P-000370",
            "pedido",
        ),
        # Remitos
        fac(
            "rem-borr-1",
            "cli-delta",
            "borrador",
            0,
            [
                _linea("prod-amo750", "Amoladora angular 750W 115mm", 1, 89900),
                _linea("prod-dis115", "Disco de corte 115×1.6mm acero", 10, 2350),
            ],
            "REM 0002-00003401",
            "remito",
        ),
        fac(
            "rem-conf-1",
            "cli-ceibo",
            "confirmado",
            1,
            [_linea("prod-lat20b", "Látex interior blanco 20L", 4, 72900)],
            "REM 0002-00003400",
            "remito",
        ),
        fac(
            "rem-conf-2",
            "cli-metal",
            "confirmado",
            2,
            [_linea("prod-cab2x15", "Cable taller 2×1.5mm rollo 100m", 2, 58900)],
            "REM 0002-00003399",
            "remito",
        ),
        fac(
            "rem-fact-1",
            "cli-pintado",
            "facturado",
            3,
            [_linea("prod-esm1l", "Esmalte sintético 1L", 8, 9600)],
            "REM 0002-00003398",
            "remito",
        ),
        # Facturas
        fac(
            "fac-conf-1",
            "cli-delta",
            "confirmado",
            0,
            [
                _linea("prod-amo750", "Amoladora angular 750W 115mm", 1, 80910),
                _linea("prod-dis115", "Disco de corte 115×1.6mm acero", 10, 2115),
                _linea("prod-guan09", "Guante nitrilo T9 par", 5, 3600),
            ],
            "FAC A 0003-00014582",
            "factura",
        ),
        fac(
            "fac-conf-2",
            "cli-anibal",
            "confirmado",
            0,
            [_linea("prod-coramk", "Correa Poly-V VW Amarok 2.0 TDI", 1, 38400)],
            "FAC B 0003-00014581",
            "factura",
        ),
        fac(
            "fac-conf-3",
            "cli-ceibo",
            "confirmado",
            8,
            [_linea("prod-lat20b", "Látex interior blanco 20L", 2, 72900)],
            "FAC A 0003-00014580",
            "factura",
        ),
        fac(
            "fac-conf-4",
            "cli-pintado",
            "confirmado",
            1,
            [_linea("prod-cinp24", "Cinta papel 24mm", 10, 1450)],
            "FAC B 0003-00014579",
            "factura",
        ),
        fac(
            "fac-borr-1",
            "cli-taller",
            "borrador",
            0,
            [_linea("prod-tal13", "Taladro percutor 13mm 650W", 1, 78500)],
            None,
            "factura",
        ),
        fac(
            "fac-mitre-mora",
            "cli-mitre",
            "confirmado",
            20,
            [
                _linea("prod-mem10", "Membrana asfáltica 10m²", 5, 28900),
                _linea("prod-tor850", "Tornillo fix 8×50 caja ×100", 8, 9400),
            ],
            "FAC A 0003-00014490",
            "factura",
        ),
    ]
    sesion.add_all(ventas)

    # Remito facturado enlazado
    ventas_origen = fac(
        "fac-desde-rem",
        "cli-pintado",
        "confirmado",
        3,
        [_linea("prod-esm1l", "Esmalte sintético 1L", 8, 9600)],
        "FAC B 0003-00014570",
        "factura",
        origen="rem-fact-1",
    )
    sesion.add(ventas_origen)

    # --- Cuenta corriente (debe/haber) ---
    cxc = [
        MovimientoCxc(
            id="cxc-1",
            cliente_id="cli-delta",
            tipo="debe",
            monto=148900.0,
            referencia_tipo="factura",
            referencia_id="fac-conf-1",
            concepto="FAC A 0003-00014582",
            fecha=HOY,
        ),
        MovimientoCxc(
            id="cxc-2",
            cliente_id="cli-delta",
            tipo="haber",
            monto=92500.0,
            referencia_tipo="recibo",
            referencia_id="rec-1",
            concepto="REC 0001-00008812",
            fecha=HOY - timedelta(days=8),
        ),
        MovimientoCxc(
            id="cxc-3",
            cliente_id="cli-delta",
            tipo="debe",
            monto=92500.0,
            referencia_tipo="factura",
            referencia_id="fac-old",
            concepto="FAC A 0003-00014390",
            fecha=HOY - timedelta(days=19),
        ),
        MovimientoCxc(
            id="cxc-4",
            cliente_id="cli-mitre",
            tipo="debe",
            monto=187400.0,
            referencia_tipo="factura",
            referencia_id="fac-mitre-mora",
            concepto="FAC A 0003-00014490 — VENCIDO",
            fecha=HOY - timedelta(days=20),
        ),
        MovimientoCxc(
            id="cxc-5",
            cliente_id="cli-ceibo",
            tipo="debe",
            monto=96800.0,
            referencia_tipo="factura",
            referencia_id="fac-conf-3",
            concepto="FAC A 0003-00014580",
            fecha=HOY - timedelta(days=8),
        ),
        MovimientoCxc(
            id="cxc-6",
            cliente_id="cli-pintado",
            tipo="debe",
            monto=12300.0,
            referencia_tipo="factura",
            referencia_id="fac-conf-4",
            concepto="FAC B 0003-00014579",
            fecha=HOY - timedelta(days=1),
        ),
        MovimientoCxc(
            id="cxc-7",
            cliente_id="cli-pintado",
            tipo="haber",
            monto=12300.0,
            referencia_tipo="recibo",
            referencia_id="rec-2",
            concepto="Cobro contado mostrador",
            fecha=HOY - timedelta(days=1),
        ),
        MovimientoCxc(
            id="cxc-8",
            cliente_id="cli-metal",
            tipo="debe",
            monto=54120.0,
            referencia_tipo="factura",
            referencia_id="fac-metal",
            concepto="Saldo parcial obra",
            fecha=HOY - timedelta(days=4),
        ),
        MovimientoCxc(
            id="cxc-9",
            cliente_id="cli-anibal",
            tipo="debe",
            monto=23450.0,
            referencia_tipo="factura",
            referencia_id="fac-conf-2",
            concepto="FAC B 0003-00014581",
            fecha=HOY,
        ),
        MovimientoCxc(
            id="cxc-10",
            cliente_id="cli-anibal",
            tipo="haber",
            monto=23450.0,
            referencia_tipo="recibo",
            referencia_id="rec-3",
            concepto="Cobrado en efectivo",
            fecha=HOY,
        ),
        # Remitos confirmados / facturados → deuda en CxC (no esperan factura)
        MovimientoCxc(
            id="cxc-rem-1",
            cliente_id="cli-ceibo",
            tipo="debe",
            monto=_imp(4 * 72900)[2],
            referencia_tipo="remito",
            referencia_id="rem-conf-1",
            concepto="REM 0002-00003400",
            fecha=HOY - timedelta(days=1),
        ),
        MovimientoCxc(
            id="cxc-rem-2",
            cliente_id="cli-metal",
            tipo="debe",
            monto=_imp(2 * 58900)[2],
            referencia_tipo="remito",
            referencia_id="rem-conf-2",
            concepto="REM 0002-00003399",
            fecha=HOY - timedelta(days=2),
        ),
        MovimientoCxc(
            id="cxc-rem-3",
            cliente_id="cli-pintado",
            tipo="debe",
            monto=_imp(8 * 9600)[2],
            referencia_tipo="remito",
            referencia_id="rem-fact-1",
            concepto="REM 0002-00003398",
            fecha=HOY - timedelta(days=3),
        ),
    ]
    sesion.add_all(cxc)

    # --- Compras ---
    def compra(
        id_: str,
        prov: str,
        tipo: str,
        estado: str,
        dias: int,
        lineas: list[LineaCompra],
        numero: str | None = None,
    ) -> Compra:
        neto = sum(l.cantidad * l.precio_unitario for l in lineas)
        n, i, t = _imp(neto)
        return Compra(
            id=id_,
            tipo=tipo,
            proveedor_id=prov,
            estado=estado,
            deposito_id="dep-1",
            fecha=HOY - timedelta(days=dias),
            neto=n,
            iva=i,
            iva_porcentaje=IVA,
            total=t,
            numero=numero,
            lineas=lineas,
        )

    compras = [
        compra(
            "fc-1",
            "prov-herrafe",
            "factura_compra",
            "confirmado",
            2,
            [
                _linea_c("prod-amo750", "Amoladora angular 750W 115mm", 5, 61900),
                _linea_c("prod-dis115", "Disco de corte 115×1.6mm acero", 100, 1480),
            ],
            "FC 0001-00001200",
        ),
        compra(
            "fc-2",
            "prov-pinturas",
            "factura_compra",
            "borrador",
            0,
            [_linea_c("prod-lat20b", "Látex interior blanco 20L", 20, 48200)],
            None,
        ),
        compra(
            "fc-3",
            "prov-electrica",
            "factura_compra",
            "confirmado",
            7,
            [_linea_c("prod-cab2x15", "Cable taller 2×1.5mm rollo 100m", 10, 38700)],
            "FC 0001-00001188",
        ),
        compra(
            "rc-1",
            "prov-herrafe",
            "remito_compra",
            "confirmado",
            1,
            [
                _linea_c("prod-tor850", "Tornillo fix 8×50 caja ×100", 30, 5900),
                _linea_c("prod-tal13", "Taladro percutor 13mm 650W", 4, 52400),
            ],
            "RP 0012-00098211",
        ),
        compra(
            "rc-2",
            "prov-pinturas",
            "remito_compra",
            "borrador",
            0,
            [_linea_c("prod-esm1l", "Esmalte sintético 1L", 24, 6200)],
            "RP 0003-00045102",
        ),
        compra(
            "rc-3",
            "prov-electrica",
            "remito_compra",
            "facturado",
            5,
            [_linea_c("prod-cab2x15", "Cable taller 2×1.5mm rollo 100m", 6, 38700)],
            "RP 0008-00012377",
        ),
    ]
    sesion.add_all(compras)

    # CxP
    sesion.add_all(
        [
            MovimientoCxp(
                id="cxp-1",
                proveedor_id="prov-herrafe",
                tipo="debe",
                monto=842300.0,
                referencia_tipo="factura_compra",
                referencia_id="fc-1",
                concepto="FC Herrafe a pagar",
                fecha=HOY - timedelta(days=2),
            ),
            MovimientoCxp(
                id="cxp-2",
                proveedor_id="prov-electrica",
                tipo="debe",
                monto=118760.0,
                referencia_tipo="factura_compra",
                referencia_id="fc-3",
                concepto="FC Eléctrica Pampeana",
                fecha=HOY - timedelta(days=7),
            ),
            MovimientoCxp(
                id="cxp-3",
                proveedor_id="prov-pinturas",
                tipo="haber",
                monto=50000.0,
                referencia_tipo="pago",
                referencia_id="pago-1",
                concepto="Pago parcial contado",
                fecha=HOY - timedelta(days=3),
            ),
        ]
    )

    # --- Caja del día ---
    sesion.add_all(
        [
            MovimientoCaja(
                id="caja-1",
                fecha=HOY,
                tipo="ingreso",
                medio="efectivo",
                monto=23450.0,
                concepto="Cobro FAC B Aníbal",
                referencia_tipo="factura",
                referencia_id="fac-conf-2",
            ),
            MovimientoCaja(
                id="caja-2",
                fecha=HOY,
                tipo="ingreso",
                medio="tarjeta",
                monto=12300.0,
                concepto="Cobro FAC B Pintado Fácil",
                referencia_tipo="factura",
                referencia_id="fac-conf-4",
            ),
            MovimientoCaja(
                id="caja-3",
                fecha=HOY,
                tipo="ingreso",
                medio="efectivo",
                monto=450000.0,
                concepto="Ventas mostrador acumuladas",
                referencia_tipo="venta",
                referencia_id="lote-hoy",
            ),
            MovimientoCaja(
                id="caja-4",
                fecha=HOY,
                tipo="egreso",
                medio="efectivo",
                monto=25000.0,
                concepto="Retiro a banco",
                referencia_tipo="retiro",
                referencia_id="ret-1",
            ),
            MovimientoCaja(
                id="caja-5",
                fecha=HOY,
                tipo="egreso",
                medio="efectivo",
                monto=8500.0,
                concepto="Gastos menores / flete",
                referencia_tipo="gasto",
                referencia_id="gas-1",
            ),
            MovimientoCaja(
                id="caja-6",
                fecha=HOY - timedelta(days=1),
                tipo="ingreso",
                medio="efectivo",
                monto=180000.0,
                concepto="Cierre día anterior",
                referencia_tipo="venta",
                referencia_id="lote-ayer",
            ),
        ]
    )

    # --- Bancos ---
    if await sesion.get(CuentaBancaria, "bco-2") is None:
        sesion.add(
            CuentaBancaria(
                id="bco-2",
                codigo="CTA-CTE",
                nombre="Cuenta corriente operativa",
                banco="Banco Nación",
                cbu="0110000000000000000002",
                es_default=False,
            )
        )
    sesion.add_all(
        [
            MovimientoBancario(
                id="bco-mov-1",
                cuenta_id="bco-1",
                fecha=HOY,
                tipo="credito",
                monto=25000.0,
                concepto="Depósito retiro de caja",
                referencia_tipo="caja",
                referencia_id="caja-4",
            ),
            MovimientoBancario(
                id="bco-mov-2",
                cuenta_id="bco-1",
                fecha=HOY - timedelta(days=2),
                tipo="debito",
                monto=118760.0,
                concepto="Pago proveedor Eléctrica",
                referencia_tipo="cxp",
                referencia_id="cxp-2",
            ),
            MovimientoBancario(
                id="bco-mov-3",
                cuenta_id="bco-2",
                fecha=HOY - timedelta(days=1),
                tipo="credito",
                monto=500000.0,
                concepto="Transferencia cliente Delta",
                referencia_tipo="cobro",
                referencia_id="cxc-2",
            ),
            ValorBancario(
                id="chq-1",
                tipo="cheque_tercero",
                estado="en_cartera",
                monto=187400.0,
                fecha=HOY - timedelta(days=5),
                fecha_vto=HOY + timedelta(days=7),
                numero="00012345",
                librador="Corralón Mitre SA",
                banco_emisor="Banco Galicia",
            ),
            ValorBancario(
                id="chq-2",
                tipo="cheque_tercero",
                estado="en_cartera",
                monto=96800.0,
                fecha=HOY - timedelta(days=2),
                fecha_vto=HOY + timedelta(days=14),
                numero="00099881",
                librador="Agropecuaria El Ceibo",
                banco_emisor="Banco Nación",
            ),
            ValorBancario(
                id="chq-3",
                tipo="cheque_tercero",
                estado="depositado",
                monto=45000.0,
                fecha=HOY - timedelta(days=10),
                fecha_vto=HOY - timedelta(days=1),
                numero="00055441",
                librador="Metalúrgica Pampa SRL",
                banco_emisor="Santander",
                cuenta_destino_id="bco-1",
            ),
            ValorBancario(
                id="chq-4",
                tipo="cheque_propio",
                estado="en_cartera",
                monto=80000.0,
                fecha=HOY,
                fecha_vto=HOY + timedelta(days=30),
                numero="P-00012",
                librador="Ventas360 Demo",
                banco_emisor="Banco Demo",
            ),
        ]
    )

    # Garantiza que los clientes serialicen con EmailStr (evita 500 en /clientes).
    from app.modulos.clientes.schemas import ClienteResponse

    await sesion.flush()
    for cli in clientes:
        ClienteResponse.model_validate(cli)

    await sesion.commit()
    return True


# Nombres para el lote de mostrador (≥50 clientes).
_NOMBRES_BULK = [
    "Corralón Los Álamos",
    "Ferretería El Tornillo",
    "Constructora Pampeana SA",
    "Obra Civil Sur SRL",
    "Pinturería Color Vivo",
    "Metalúrgica del Valle",
    "Agroservicios La Esperanza",
    "Distribuidora Trebol",
    "Electricidad Central",
    "Sanitarios Pico",
    "Herramientas Express",
    "Corralón Ruta 5",
    "Vidrios y Aluminios Norte",
    "Plomería Don José",
    "Taller Mecánico Atlas",
    "Carpintería Maderera",
    "Insumos Industriales SA",
    "Ferretería 9 de Julio",
    "Construcciones Beta",
    "Servicios Municipales Obras",
    "Cooperativa El Progreso",
    "Mayorista del Centro",
    "Ferretería La Esquina",
    "Corralón Hermosilla",
    "Pinturas del Sur",
    "Soldaduras Pampa",
    "Maquinarias Rojas",
    "Depósito Industrial Oeste",
    "Fijaciones Seguras SRL",
    "Iluminación LED Pico",
    "Cerrajería Moderna",
    "Abrasivos del Centro",
    "Hidráulica Rural",
    "Repuestos Automotrices KM",
    "Obra Pública Zona Norte",
    "Ferretería Familiar Gómez",
    "Corralón Tres Hermanos",
    "Constructora Horizonte",
    "Agroquímicos del Campo",
    "Distribuidora Omega",
    "Materiales El Puente",
    "Ferretería San Cayetano",
    "Talleres Unidos SRL",
    "Pinturería Artística",
    "Electricar Pampeana",
    "Corralón Barrio Norte",
    "Insumos de Obra Max",
    "Ferretería Don Pedro",
    "Constructora Río Salado",
    "Mayorista Herramientas BA",
    "Servicios Técnicos Luna",
    "Corralón La Estación",
    "Ferretería Mitre 1200",
    "Obras y Reformas SA",
]


async def asegurar_casuistica_mostrador(sesion: AsyncSession) -> bool:
    """≥50 clientes con remito (≥5 ítems) y cta. cte. debe / a favor.

    Idempotente: marcador `cli-bulk-01`.
    """
    from sqlalchemy import select

    from app.modulos.clientes.schemas import ClienteResponse

    if await sesion.get(Cliente, "cli-bulk-01") is not None:
        return False

    productos = (
        await sesion.execute(
            select(Producto).where(Producto.activo.is_(True)).order_by(Producto.sku).limit(40)
        )
    ).scalars().all()
    if len(productos) < 5:
        raise RuntimeError(
            "Se necesitan al menos 5 productos activos para la casuística de mostrador"
        )

    zonas = (
        await sesion.execute(select(Zona).where(Zona.activo.is_(True)))
    ).scalars().all()
    zona_ids = [z.id for z in zonas] or [None]
    vendedor_ids = ["usr-vendedor-1", "usr-vendedor-2"]

    clientes_bulk: list[Cliente] = []
    remitos: list[Pedido] = []
    cxc: list[MovimientoCxc] = []

    n = max(50, len(_NOMBRES_BULK))
    for i in range(1, n + 1):
        cid = f"cli-bulk-{i:02d}"
        nombre = _NOMBRES_BULK[(i - 1) % len(_NOMBRES_BULK)]
        if i > len(_NOMBRES_BULK):
            nombre = f"{nombre} {i}"
        # Email válido (EmailStr); dominio realista .com.ar
        email = f"cliente.bulk.{i:02d}@ventas360.com.ar"
        cuit = f"30{70000000 + i:08d}"[:11]
        # Variar condición IVA
        ivas = [
            "responsable_inscripto",
            "responsable_inscripto",
            "monotributo",
            "exento",
            "consumidor_final",
        ]
        cli = Cliente(
            id=cid,
            nombre=nombre if i <= len(_NOMBRES_BULK) else f"Cliente bulk {i:02d} — {nombre}",
            email=email,
            telefono=f"02302 4{i:04d}",
            cuit=cuit,
            condicion_iva=ivas[i % len(ivas)],
            limite_credito=float(50_000 + (i % 10) * 25_000),
            zona_id=zona_ids[i % len(zona_ids)],
            vendedor_id=vendedor_ids[i % len(vendedor_ids)],
            bloqueado=False,
            activo=True,
            observaciones=f"Casuística mostrador #{i}",
        )
        clientes_bulk.append(cli)

        # Remito confirmado con ≥5 productos
        n_lineas = 5 + (i % 4)  # 5..8
        lineas: list[LineaPedido] = []
        for j in range(n_lineas):
            p = productos[(i + j) % len(productos)]
            qty = 1 + ((i + j) % 5)
            lineas.append(
                _linea(p.id, p.nombre[:120], qty, float(p.precio))
            )
        neto = sum(l.cantidad * l.precio_unitario for l in lineas)
        n_, iva_, tot_ = _imp(neto)
        remitos.append(
            Pedido(
                id=f"rem-bulk-{i:02d}",
                tipo="remito",
                cliente_id=cid,
                estado="confirmado",
                deposito_id="dep-1",
                fecha=HOY - timedelta(days=(i % 28)),
                neto=n_,
                iva=iva_,
                iva_porcentaje=IVA,
                total=tot_,
                numero=f"REM 0002-{10000 + i:08d}",
                lineas=lineas,
            )
        )

        # CxC: ~40% debe, ~35% a favor, ~25% al día (saldo 0 con movimientos)
        grupo = i % 10
        if grupo < 4:
            # Debe (saldo > 0) — deuda del remito emitido (aún sin factura)
            debe = tot_
            cxc.append(
                MovimientoCxc(
                    id=f"cxc-bulk-d-{i:02d}",
                    cliente_id=cid,
                    tipo="debe",
                    monto=debe,
                    referencia_tipo="remito",
                    referencia_id=f"rem-bulk-{i:02d}",
                    concepto=f"REM 0002-{10000 + i:08d}",
                    fecha=HOY - timedelta(days=(i % 20)),
                )
            )
            if i % 3 == 0:
                # Pago parcial (sigue debiendo)
                cxc.append(
                    MovimientoCxc(
                        id=f"cxc-bulk-hp-{i:02d}",
                        cliente_id=cid,
                        tipo="haber",
                        monto=round(debe * 0.35, 2),
                        referencia_tipo="recibo",
                        referencia_id=f"rec-bulk-{i:02d}",
                        concepto=f"Cobro parcial bulk {i:02d}",
                        fecha=HOY - timedelta(days=(i % 10)),
                    )
                )
        elif grupo < 8:
            # A favor (saldo < 0) — verde ↑ en mostrador
            anticipo = round(8_000 + i * 900 + (i % 5) * 400, 2)
            cxc.append(
                MovimientoCxc(
                    id=f"cxc-bulk-h-{i:02d}",
                    cliente_id=cid,
                    tipo="haber",
                    monto=anticipo,
                    referencia_tipo="recibo",
                    referencia_id=f"rec-fav-{i:02d}",
                    concepto=f"Anticipo / NC bulk {i:02d}",
                    fecha=HOY - timedelta(days=(i % 15)),
                )
            )
            if i % 4 == 0:
                # Pequeño debe que no cubre el haber
                cxc.append(
                    MovimientoCxc(
                        id=f"cxc-bulk-df-{i:02d}",
                        cliente_id=cid,
                        tipo="debe",
                        monto=round(anticipo * 0.25, 2),
                        referencia_tipo="factura",
                        referencia_id=f"fac-fav-{i:02d}",
                        concepto=f"FAC parcial contra anticipo {i:02d}",
                        fecha=HOY - timedelta(days=(i % 8)),
                    )
                )
        else:
            # Al día: debe = haber
            monto = round(12_000 + i * 300, 2)
            cxc.append(
                MovimientoCxc(
                    id=f"cxc-bulk-z-d-{i:02d}",
                    cliente_id=cid,
                    tipo="debe",
                    monto=monto,
                    referencia_tipo="factura",
                    referencia_id=f"fac-zd-{i:02d}",
                    concepto=f"FAC saldada bulk {i:02d}",
                    fecha=HOY - timedelta(days=12),
                )
            )
            cxc.append(
                MovimientoCxc(
                    id=f"cxc-bulk-z-h-{i:02d}",
                    cliente_id=cid,
                    tipo="haber",
                    monto=monto,
                    referencia_tipo="recibo",
                    referencia_id=f"rec-zd-{i:02d}",
                    concepto=f"Cobro total bulk {i:02d}",
                    fecha=HOY - timedelta(days=5),
                )
            )

    for cli in clientes_bulk:
        ClienteResponse.model_validate(cli)

    sesion.add_all(clientes_bulk)
    sesion.add_all(remitos)
    sesion.add_all(cxc)
    await sesion.commit()
    return True


async def asegurar_cxc_remitos_emitidos(sesion: AsyncSession) -> int:
    """Alinea CxC con remitos emitidos (confirmado/facturado) en bases ya sembradas.

    - Inserta debe por remito si falta.
    - Reescribe deudas bulk `fac-bulk-*` → `rem-bulk-*`.
    Devuelve cantidad de movimientos tocados.
    """
    from sqlalchemy import select

    tocados = 0

    # 1) Bulk legacy: fac-bulk-XX → remito correspondiente
    for i in range(1, 60):
        mov = await sesion.get(MovimientoCxc, f"cxc-bulk-d-{i:02d}")
        if mov is None:
            continue
        if mov.referencia_tipo == "remito" and mov.referencia_id.startswith("rem-bulk-"):
            continue
        rem = await sesion.get(Pedido, f"rem-bulk-{i:02d}")
        if rem is None:
            continue
        mov.referencia_tipo = "remito"
        mov.referencia_id = rem.id
        mov.concepto = rem.numero or f"Remito {rem.id[:8]}"
        mov.monto = rem.total
        tocados += 1

    # 2) Remitos demo + cualquier otro sin movimiento CxC
    remitos = (
        await sesion.execute(
            select(Pedido).where(
                Pedido.tipo == "remito",
                Pedido.estado.in_(("confirmado", "facturado")),
            )
        )
    ).scalars().all()

    for rem in remitos:
        ya = (
            await sesion.execute(
                select(MovimientoCxc.id).where(
                    MovimientoCxc.referencia_tipo == "remito",
                    MovimientoCxc.referencia_id == rem.id,
                )
            )
        ).scalar_one_or_none()
        if ya is not None:
            continue

        # Legacy: si ya hay debe por la factura hija, no duplicar
        fac = (
            await sesion.execute(
                select(Pedido).where(
                    Pedido.tipo == "factura",
                    Pedido.origen_id == rem.id,
                )
            )
        ).scalar_one_or_none()
        if fac is not None:
            fac_cxc = (
                await sesion.execute(
                    select(MovimientoCxc.id).where(
                        MovimientoCxc.referencia_tipo == "factura",
                        MovimientoCxc.referencia_id == fac.id,
                    )
                )
            ).scalar_one_or_none()
            if fac_cxc is not None:
                continue

        sesion.add(
            MovimientoCxc(
                id=f"cxc-sync-{rem.id[:18]}",
                cliente_id=rem.cliente_id,
                tipo="debe",
                monto=rem.total,
                referencia_tipo="remito",
                referencia_id=rem.id,
                concepto=rem.numero or f"Remito {rem.id[:8]}",
                fecha=rem.fecha,
            )
        )
        tocados += 1

    if tocados:
        await sesion.commit()
    return tocados
