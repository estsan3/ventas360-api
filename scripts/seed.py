"""Seed mínimo de datos de demo.

Se ejecuta automáticamente al iniciar la API en dev (si la base está vacía)
o manualmente con:
    poetry run python -m scripts.seed
"""

import asyncio
from datetime import date

from app.core.database import crear_tablas, fabrica_sesiones
from app.core.seguridad import hashear_password
from app.modulos.auth.dao import UsuarioDAO
from app.modulos.auth.models import Usuario
from app.modulos.clientes.models import Cliente
from app.modulos.productos.models import Producto
from app.modulos.ventas.models import LineaPedido, Pedido

EMAIL_DEMO = "admin@ventas360.com"
PASSWORD_DEMO = "demo12345"


async def sembrar_datos_demo() -> None:
    """Inserta admin, vendedor, clientes, productos y pedidos de demo."""
    async with fabrica_sesiones() as sesion:
        dao = UsuarioDAO(sesion)
        if await dao.buscar_por_email(EMAIL_DEMO) is not None:
            return

        password_hash = hashear_password(PASSWORD_DEMO)
        sesion.add(
            Usuario(
                nombre="Admin Demo",
                dni="20111222",
                email=EMAIL_DEMO,
                password_hash=password_hash,
                rol="administrador",
            )
        )
        sesion.add(
            Usuario(
                nombre="Vendedor Demo",
                dni="30123456",
                email="vendedor@ventas360.com",
                password_hash=password_hash,
                rol="vendedor",
            )
        )
        await sesion.flush()

        clientes = [
            Cliente(
                id="cli-1",
                nombre="María López",
                email="maria.lopez@email.com",
                telefono="+54 11 5555-1001",
            ),
            Cliente(
                id="cli-2",
                nombre="Comercio San Martín",
                email="contacto@sanmartin.com.ar",
                telefono="+54 341 555-2200",
            ),
            Cliente(
                id="cli-3",
                nombre="Distribuidora Norte",
                email="ventas@norte.com.ar",
                telefono="+54 11 5555-3300",
            ),
        ]
        sesion.add_all(clientes)

        productos = [
            Producto(id="prod-1", sku="NB-001", nombre="Notebook 14\"", precio=850000.0, stock=12),
            Producto(id="prod-2", sku="MS-010", nombre="Mouse inalámbrico", precio=18500.0, stock=45),
            Producto(id="prod-3", sku="TK-200", nombre="Teclado mecánico", precio=42000.0, stock=20),
            Producto(id="prod-4", sku="MN-027", nombre="Monitor 27\"", precio=320000.0, stock=8),
        ]
        sesion.add_all(productos)
        await sesion.flush()

        pedido1 = Pedido(
            id="ped-1",
            cliente_id="cli-1",
            estado="confirmado",
            fecha=date.today(),
            total=868500.0,
            lineas=[
                LineaPedido(producto_id="prod-1", cantidad=1, precio_unitario=850000.0),
                LineaPedido(producto_id="prod-2", cantidad=1, precio_unitario=18500.0),
            ],
        )
        pedido2 = Pedido(
            id="ped-2",
            cliente_id="cli-2",
            estado="entregado",
            fecha=date.today(),
            total=362000.0,
            lineas=[
                LineaPedido(producto_id="prod-4", cantidad=1, precio_unitario=320000.0),
                LineaPedido(producto_id="prod-3", cantidad=1, precio_unitario=42000.0),
            ],
        )
        sesion.add_all([pedido1, pedido2])

        await sesion.commit()


if __name__ == "__main__":
    async def _main() -> None:
        await crear_tablas()
        await sembrar_datos_demo()
        print(f"Seed listo. Login demo: {EMAIL_DEMO} / {PASSWORD_DEMO}")

    asyncio.run(_main())
