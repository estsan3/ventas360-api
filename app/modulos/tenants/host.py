"""Lectura del hostname del request (proxy Angular vs API directa).

El proxy reescribe `Host` a localhost:8001. El subdominio real llega en
`Origin` o `X-Forwarded-Host`.
"""

from urllib.parse import urlparse

from fastapi import Request


def hostname_desde_request(request: Request) -> str:
    """Hostname con puerto si aplica, listo para clasificar en el BO."""
    forwarded = request.headers.get("x-forwarded-host") or request.headers.get(
        "x-original-host"
    )
    if forwarded:
        return forwarded.split(",")[0].strip()

    origin = request.headers.get("origin")
    if origin:
        parsed = urlparse(origin)
        if parsed.hostname:
            if parsed.port:
                return f"{parsed.hostname}:{parsed.port}"
            return parsed.hostname

    return (request.headers.get("host") or "").strip()
