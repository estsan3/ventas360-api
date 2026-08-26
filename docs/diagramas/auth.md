# auth — login

Fuente: `app/modulos/auth/` · Flujo principal: `POST /api/v1/auth/login`.
Actualizado: 2026-08-26.

Valida credenciales, que el Host coincida con el tenant del usuario (o plataforma para `superadmin`) y emite JWT en cookie httpOnly + body.

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
    Tenants-->>Service: tipo plataforma/comercio + tenant_id
    Service->>BO: validar_login_host
    Service->>JWT: crear_token_acceso sub, email, rol, tenant_id
    alt usuario con tenant_id
        Service->>Tenants: modulos_habilitados(tenant_id, rol)
        Tenants-->>Service: permisos
    end
    Service-->>Router: LoginResponse token + usuario
    Router->>Router: Set-Cookie httpOnly
    Router-->>Cliente: 200 LoginResponse
```

## Otros endpoints

| Método | Ruta | operation_id |
|--------|------|----------------|
| GET | `/auth/me` | `obtener_perfil` |
| POST | `/auth/logout` | `logout` (borra cookie) |
| GET/POST/DELETE | `/usuarios` | listar / crear / eliminar |
| GET/POST/DELETE | `/catalogos/vendedores` | vendedores (usuarios rol vendedor) |

## Contrato público

`ContratoAuth`: `existe_usuario`, `listar_por_rol`, `crear_administrador_inicial`, `listar_usuarios_de_tenant`, `primeros_administradores`, `cambiar_password_de_tenant`. Usado por **tenants** y **clientes**.
