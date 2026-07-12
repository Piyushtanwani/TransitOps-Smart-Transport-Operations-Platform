"""Domain error hierarchy + exception handlers producing the docs/03 §2 envelope."""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class APIError(Exception):
    """Base error carrying a machine code, human message, optional field, HTTP status."""

    status_code: int = 400

    def __init__(
        self,
        code: str,
        message: str,
        field: str | None = None,
        status_code: int | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.field = field
        if status_code is not None:
            self.status_code = status_code
        super().__init__(message)


class DomainError(APIError):
    """Business-rule conflict → 409 (unless an explicit status is supplied, e.g. 503)."""

    status_code = 409


class NotFoundError(APIError):
    """Missing resource → 404 `NOT_FOUND`."""

    status_code = 404

    def __init__(self, resource: str) -> None:
        super().__init__("NOT_FOUND", f"{resource.capitalize()} not found.")


class AuthError(APIError):
    """Authentication failure → 401."""

    status_code = 401


class ForbiddenError(APIError):
    """Role not permitted → 403 `FORBIDDEN_ROLE`."""

    status_code = 403

    def __init__(
        self, message: str = "You do not have permission to perform this action."
    ) -> None:
        super().__init__("FORBIDDEN_ROLE", message)


def _envelope(code: str, message: str, field: str | None) -> dict:
    return {"error": {"code": code, "message": message, "field": field}}


_HTTP_CODE = {
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
}


def register_exception_handlers(app: FastAPI) -> None:
    """Wire every error path onto the single global envelope shape."""

    @app.exception_handler(APIError)
    async def _api_error(_: Request, exc: APIError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope(exc.code, exc.message, exc.field),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        errors = exc.errors()
        field: str | None = None
        message = "Validation failed."
        if errors:
            first = errors[0]
            loc = [p for p in first.get("loc", ()) if p not in ("body", "query", "path")]
            field = str(loc[-1]) if loc else None
            message = first.get("msg", message)
            # Pydantic prefixes value errors with "Value error, " — strip for readability.
            message = message.replace("Value error, ", "")
        return JSONResponse(
            status_code=422, content=_envelope("VALIDATION_ERROR", message, field)
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = _HTTP_CODE.get(exc.status_code, "HTTP_ERROR")
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope(code, str(exc.detail), None),
        )
