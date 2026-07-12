"""Domain error hierarchy + exception handlers producing the docs/03 §2 envelope."""
from __future__ import annotations

import logging

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
            message = _humanize(first, field)
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

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
        # Never leak internals to the client; full traceback goes to the server log.
        logging.getLogger("transitops").exception("Unhandled error", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content=_envelope(
                "INTERNAL_ERROR", "Something went wrong on our side. Please try again.", None
            ),
        )


def _label(field: str | None) -> str:
    return (field or "This field").replace("_", " ").strip().capitalize()


def _humanize(err: dict, field: str | None) -> str:
    """Turn Pydantic's technical messages into plain, user-friendly language."""
    kind = err.get("type", "")
    ctx = err.get("ctx", {}) or {}
    label = _label(field)
    friendly = {
        "missing": f"{label} is required.",
        "string_too_short": f"{label} is too short.",
        "string_too_long": f"{label} is too long.",
        "string_pattern_mismatch": f"{label} has an invalid format.",
        "value_error": None,  # handled below (custom validators carry their own text)
        "greater_than": f"{label} must be greater than {ctx.get('gt', 0)}.",
        "greater_than_equal": f"{label} must be at least {ctx.get('ge', 0)}.",
        "less_than": f"{label} must be less than {ctx.get('lt', '')}.",
        "less_than_equal": f"{label} must be at most {ctx.get('le', '')}.",
        "int_parsing": f"{label} must be a whole number.",
        "float_parsing": f"{label} must be a number.",
        "decimal_parsing": f"{label} must be a number.",
        "bool_parsing": f"{label} must be true or false.",
        "uuid_parsing": f"{label} is not a valid ID.",
        "date_from_datetime_parsing": f"{label} must be a valid date (YYYY-MM-DD).",
        "date_parsing": f"{label} must be a valid date (YYYY-MM-DD).",
        "datetime_from_date_parsing": f"{label} must be a valid date.",
        "enum": f"{label} must be one of: {ctx.get('expected', 'the allowed values')}.",
        "literal_error": f"{label} must be one of: {ctx.get('expected', 'the allowed values')}.",
        "json_invalid": "The request body is not valid JSON.",
    }
    mapped = friendly.get(kind)
    if mapped:
        return mapped
    raw = err.get("msg", "Validation failed.")
    # Custom validators ("Value error, <text>") already carry human wording — keep it.
    if raw.startswith("Value error, "):
        return raw.removeprefix("Value error, ")
    if kind == "value_error.email" or "email address" in raw.lower():
        return "Enter a valid email address."
    return raw
