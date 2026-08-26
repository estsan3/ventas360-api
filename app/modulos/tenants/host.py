"""Lectura del hostname del request (proxy Angular vs API directa).

El proxy reescribe `Host` a localhost:8001. El subdominio real llega en
`X-Forwarded-Host`, `Origin` o `Referer` (GET same-origin no manda Origin).
"""

from urllib.parse import urlparse

from fastapi import Request


def _host_de_url(valor: str) -> str:
    parsed = urlparse(valor)
    if not parsed.hostname:
        return ""
    if parsed.port:
        return f"{parsed.hostname}:{parsed.port}"
    return parsed.hostname


def hostname_desde_request(request: Request) -> str:
    """Hostname con puerto si aplica, listo para clasificar en el BO."""
    forwarded = request.headers.get("x-forwarded-host") or request.headers.get(
        "x-original-host"
    )
    if forwarded:
        return forwarded.split(",")[0].strip()

    origin = _host_de_url(request.headers.get("origin") or "")
    if origin:
        return origin

    referer = _host_de_url(request.headers.get("referer") or "")
    if referer:
        return referer

    return (request.headers.get("host") or "").strip()
