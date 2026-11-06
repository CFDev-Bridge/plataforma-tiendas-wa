"""Middlewares HTTP transversales: identificador de petición, log de acceso y cabeceras."""

import logging
from collections.abc import Awaitable, Callable
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request, Response

from app.core.logging import log_fields, request_id_var

REQUEST_ID_HEADER = "X-Request-ID"

SECURITY_HEADERS: dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
}

_access_logger = logging.getLogger("app.access")

CallNext = Callable[[Request], Awaitable[Response]]


async def request_context_middleware(request: Request, call_next: CallNext) -> Response:
    # El identificador se genera siempre en el servidor; no se confía en el que envía el cliente.
    request_id = uuid4().hex
    token = request_id_var.set(request_id)
    started = perf_counter()
    try:
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        _access_logger.info(
            "http_request",
            extra=log_fields(
                method=request.method,
                path=request.url.path,
                status=response.status_code,
                duration_ms=round((perf_counter() - started) * 1000, 2),
            ),
        )
        return response
    finally:
        request_id_var.reset(token)


async def security_headers_middleware(request: Request, call_next: CallNext) -> Response:
    response = await call_next(request)
    for name, value in SECURITY_HEADERS.items():
        response.headers.setdefault(name, value)
    return response


def register_middlewares(app: FastAPI) -> None:
    # Starlette ejecuta primero el último registrado: el contexto de petición envuelve todo.
    app.middleware("http")(security_headers_middleware)
    app.middleware("http")(request_context_middleware)
