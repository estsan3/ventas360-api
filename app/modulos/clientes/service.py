"""Capa SERVICE del módulo clientes."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.excepciones import RecursoNoEncontrado, ReglaDeNegocioViolada
from app.modulos.auth.contrato import AuthLocal, ContratoAuth
from app.modulos.clientes.bo import ClienteBO
from app.modulos.clientes.dao import ClienteDAO
from app.modulos.clientes.models import Cliente
from app.modulos.clientes.schemas import (
    ActualizarClienteRequest,
    ClienteResponse,
    ClientesPaginaResponse,
    CrearClienteRequest,
)
from app.modulos.zonas.contrato import ContratoZonas, ZonasLocal


class ClientesService:
    """Casos de uso de clientes."""

    def __init__(
        self,
        sesion: AsyncSession,
        auth: ContratoAuth | None = None,
        zonas: ContratoZonas | None = None,
    ) -> None:
        self._sesion = sesion
        self._dao = ClienteDAO(sesion)
        self._bo = ClienteBO()
        self._auth = auth or AuthLocal(sesion)
        self._zonas = zonas or ZonasLocal(sesion)

    async def listar(
        self,
        *,
        q: str | None = None,
        activo: bool | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> ClientesPaginaResponse:
        items, total = await self._dao.listar(
            q=q, activo=activo, page=page, page_size=page_size
        )
        return ClientesPaginaResponse(
            items=[ClienteResponse.model_validate(c) for c in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def obtener(self, cliente_id: str) -> ClienteResponse:
        cliente = await self._buscar_o_fallar(cliente_id)
        return ClienteResponse.model_validate(cliente)

    async def crear(self, datos: CrearClienteRequest) -> ClienteResponse:
        existente = await self._dao.buscar_por_email(str(datos.email))
        self._bo.validar_alta(email_ya_registrado=existente is not None)
        self._bo.validar_datos_comerciales(
            datos.cuit, datos.condicion_iva, datos.limite_credito
        )
        await self._validar_vendedor(datos.vendedor_id)
        await self._validar_zona(datos.zona_id)

        cliente = Cliente(
            nombre=datos.nombre,
            email=str(datos.email),
            telefono=datos.telefono,
            cuit=datos.cuit.replace("-", "").strip(),
            condicion_iva=datos.condicion_iva,
            limite_credito=datos.limite_credito,
            zona_id=datos.zona_id,
            vendedor_id=datos.vendedor_id,
            bloqueado=datos.bloqueado,
            observaciones=datos.observaciones,
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

        cuit = datos.cuit if datos.cuit is not None else cliente.cuit
        condicion = (
            datos.condicion_iva
            if datos.condicion_iva is not None
            else cliente.condicion_iva
        )
        limite = (
            datos.limite_credito
            if datos.limite_credito is not None
            else cliente.limite_credito
        )
        self._bo.validar_datos_comerciales(cuit, condicion, limite)

        if datos.vendedor_id is not None:
            await self._validar_vendedor(datos.vendedor_id)
            cliente.vendedor_id = datos.vendedor_id

        if datos.nombre is not None:
            cliente.nombre = datos.nombre
        if datos.telefono is not None:
            cliente.telefono = datos.telefono
        if datos.cuit is not None:
            cliente.cuit = datos.cuit.replace("-", "").strip()
        if datos.condicion_iva is not None:
            cliente.condicion_iva = datos.condicion_iva
        if datos.limite_credito is not None:
            cliente.limite_credito = datos.limite_credito
        if datos.zona_id is not None:
            await self._validar_zona(datos.zona_id)
            cliente.zona_id = datos.zona_id
        if datos.bloqueado is not None:
            cliente.bloqueado = datos.bloqueado
        if datos.observaciones is not None:
            cliente.observaciones = datos.observaciones

        await self._sesion.commit()
        return ClienteResponse.model_validate(cliente)

    async def desactivar(self, cliente_id: str) -> ClienteResponse:
        cliente = await self._buscar_o_fallar(cliente_id)
        self._bo.validar_baja(cliente.activo)
        cliente.activo = False
        await self._sesion.commit()
        return ClienteResponse.model_validate(cliente)

    async def _validar_vendedor(self, vendedor_id: str | None) -> None:
        if not vendedor_id:
            return
        existe = await self._auth.existe_usuario(vendedor_id)
        self._bo.validar_vendedor(vendedor_id, existe)

    async def _validar_zona(self, zona_id: str | None) -> None:
        if not zona_id:
            return
        if not await self._zonas.existe_zona(zona_id):
            raise ReglaDeNegocioViolada("La zona indicada no existe o está inactiva")

    async def _buscar_o_fallar(self, cliente_id: str) -> Cliente:
        cliente = await self._dao.buscar_por_id(cliente_id)
        if cliente is None:
            raise RecursoNoEncontrado("Cliente no encontrado")
        return cliente
