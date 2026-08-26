# auth — login por Host

Prefijo: `/api/v1/auth`, `/api/v1/usuarios`, `/api/v1/catalogos/vendedores`.
Fuentes: `app/modulos/auth/{router,service,bo,dao,contrato}.py`, `app/core/seguridad.py`.

## POST /auth/login (`operation_id`: `login`)

```mermaid
sequenceDiagram
    autonumber
    participant ClienteHTTP
    participant AuthRouter
    participant AuthService
    participant UsuarioDAO
    participant UsuarioBO
    participant ContratoTenants
    participant JWT

    ClienteHTTP->>AuthRouter: POST /auth/login (email, password) + Host
    AuthRouter->>AuthRouter: hostname_desde_request
    AuthRouter->>AuthService: login(datos, host)
    AuthService->>UsuarioDAO: buscar_por_email(email)
    UsuarioDAO-->>AuthService: Usuario o None
    AuthService->>UsuarioBO: validar_credenciales(hash, password)
    AuthService->>ContratoTenants: contexto_desde_host(host)
    ContratoTenants-->>AuthService: tipo_host + tenant_id_host
    AuthService->>UsuarioBO: validar_login_host
    Note over UsuarioBO: superadmin solo en admin.* comercio exige mismo tenant
    AuthService->>JWT: crear_token_acceso(sub, email, rol, tenant_id)
    JWT-->>AuthService: access_token
    AuthService->>ContratoTenants: modulos_habilitados(tenant_id, rol)
    AuthService-->>AuthRouter: LoginResponse
    AuthRouter->>AuthRouter: Set-Cookie ventas360_access_token httpOnly
    AuthRouter-->>ClienteHTTP: 200 + JWT en cookie y body
```

## Otros endpoints

| Método | Path | operation_id |
|--------|------|--------------|
| GET | `/auth/me` | `obtener_perfil` |
| POST | `/auth/logout` | `logout` (borra cookie, sin DB) |
| GET/POST | `/usuarios` | `listar_usuarios` / `crear_usuario` |
| GET/POST | `/catalogos/vendedores` | `listar_vendedores` / `crear_vendedor` |

Contrato expuesto: `ContratoAuth` (admin inicial, existe_usuario). Usa `ContratoTenants`.
