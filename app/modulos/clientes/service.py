"""Capa SERVICE del módulo clientes."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.excepciones import RecursoNoEncontrado
from app.modulos.clientes.bo import ClienteBO
from app.modulos.clientes.dao import ClienteDAO
from app.modulos.clientes.models import Cliente
from app.modulos.clientes.schemas import (
    ActualizarClienteRequest,
    ClienteResponse,
    CrearClienteRequest,
)


class ClientesService:
    """Casos de uso de clientes."""

    def __init__(self, sesion: AsyncSession) -> None:
        self._sesion = sesion
        self._dao = ClienteDAO(sesion)
        self._bo = ClienteBO()

    async def listar(self) -> list[ClienteResponse]:
        clientes = await self._dao.listar()
        return [ClienteResponse.model_validate(c) for c in clientes]

    async def obtener(self, cliente_id: str) -> ClienteResponse:
        cliente = await self._buscar_o_fallar(cliente_id)
        return ClienteResponse.model_validate(cliente)

    async def crear(self, datos: CrearClienteRequest) -> ClienteResponse:
        existente = await self._dao.buscar_por_email(str(datos.email))
        self._bo.validar_alta(email_ya_registrado=existente is not None)

        cliente = Cliente(
            nombre=datos.nombre,
            email=str(datos.email),
            telefono=datos.telefono,
        )
        await self._dao.guardar(cliente)
        await self._sesion.commit()
        return ClienteResponse.model_validate(cliente)

    async def actualizar(
        self, cliente_id: str, datos: ActualizarClienteRequest
    ) -> ClienteResponse:
        cliente = await self._buscar_o_fallar(cliente_id)

        if datos.email is not None and str(datos.email) != cliente.email:
            existente = await self._dao.buscar_por_email(str(datos.email))
            self._bo.validar_alta(email_ya_registrado=existente is not None)
            cliente.email = str(datos.email)
        if datos.nombre is not None:
            cliente.nombre = datos.nombre
        if datos.telefono is not None:
            cliente.telefono = datos.telefono

        await self._sesion.commit()
        return ClienteResponse.model_validate(cliente)

    async def desactivar(self, cliente_id: str) -> ClienteResponse:
        cliente = await self._buscar_o_fallar(cliente_id)
        self._bo.validar_baja(cliente)
        cliente.activo = False
        await self._sesion.commit()
        return ClienteResponse.model_validate(cliente)

    async def _buscar_o_fallar(self, cliente_id: str) -> Cliente:
        cliente = await self._dao.buscar_por_id(cliente_id)
        if cliente is None:
            raise RecursoNoEncontrado("Cliente no encontrado")
        return cliente
