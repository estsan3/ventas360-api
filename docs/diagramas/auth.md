# auth — login

Fuente: `app/modulos/auth/` · Flujo principal: `POST /api/v1/auth/login`.
Actualizado: 2026-09-26.

Valida credenciales, que el Host coincida con el tenant del usuario (o plataforma para `superadmin`) y emite JWT en cookie httpOnly + body. No hay `commit` en el login.

```mermaid
sequenceDiagram
    participant Cliente
    participant Router as auth.router
    participant Service as AuthService
    participant DAO as UsuarioDAO
    participant BO as UsuarioBO
    participant Tenants as ContratoTenants
    participant JWT as core.seguridad

    Cliente->>Router: POST /auth/login email, password + Host
    Router->>Service: login(datos, host)
    Service->>DAO: buscar_por_email
    DAO-->>Service: Usuario o None
    Service->>BO: validar_credenciales
    Service->>Tenants: contexto_desde_host(host)
    Tenants-->>Service: tipo plataforma, comercio o sin_slug
    Service->>BO: validar_login_host
    Note over BO: sin_slug u host ajeno → NoAutenticado
    Service->>JWT: crear_token_acceso sub, email, rol, tenant_id
    alt usuario con tenant_id
        Service->>Tenants: modulos_habilitados(tenant_id, rol)
        Tenants-->>Service: permisos
    end
    Service-->>Router: LoginResponse token + usuario
    Router->>Router: Set-Cookie httpOnly
    Router-->>Cliente: 200 LoginResponse
```

`GET /auth/me` repite Host + `modulos_habilitados`. El alta de usuario asigna password inicial `cambiar12345` si el front no manda una. El alta rápida de vendedor crea email provisorio `vendedor-{uuid}@pendiente.ventas360`.

## Otros endpoints

| Método | Ruta | operation_id |
|--------|------|----------------|
| POST | `/auth/login` | `login` |
| GET | `/auth/me` | `obtener_perfil` |
| POST | `/auth/logout` | `logout` (borra cookie) |
| GET | `/usuarios` | `listar_usuarios` |
| POST | `/usuarios` | `crear_usuario` |
| DELETE | `/usuarios/{id}` | `eliminar_usuario` |
| GET | `/catalogos/vendedores` | `listar_vendedores` |
| POST | `/catalogos/vendedores` | `crear_vendedor` |
| DELETE | `/catalogos/vendedores/{id}` | `eliminar_vendedor` |

Usuarios y vendedores exigen módulo `configuracion` (listar vendedores también acepta `clientes`, `mostrador`, `cta_cte`, `ventas`).

## Contrato público

`ContratoAuth`: `existe_usuario`, `listar_por_rol`, `crear_administrador_inicial`, `listar_usuarios_de_tenant`, `primeros_administradores`, `cambiar_password_de_tenant`. Usado por **tenants** y **clientes**.
