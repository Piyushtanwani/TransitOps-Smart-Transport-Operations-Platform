"""FastAPI application factory: CORS, error handlers, routers, health check."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import engine


def _db_status() -> str:
    """Report DB reachability for the health probe (never raises)."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return "up"
    except Exception:
        return "down"


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="TransitOps API",
        version="0.1.0",
        description="Transport operations platform — vehicles, drivers, trips, maintenance, AI.",
        openapi_url="/api/v1/openapi.json",
        docs_url="/docs",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1024)

    @app.middleware("http")
    async def security_headers(request, call_next):  # industry-standard response headers
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault(
            "Cache-Control", "no-store" if request.url.path.startswith("/api/") else "no-cache"
        )
        return response

    from app.core.errors import register_exception_handlers

    register_exception_handlers(app)

    # Domain routers are mounted as each BE task lands them.
    _mount_routers(app)

    @app.get("/api/v1/health", tags=["Health"], summary="Liveness + DB probe")
    def health() -> dict[str, str]:
        return {"status": "ok", "db": _db_status()}

    return app


def _mount_routers(app: FastAPI) -> None:
    """Include domain routers when present (kept import-safe during scaffolding)."""
    try:
        from app.api.v1 import api_router

        app.include_router(api_router, prefix="/api/v1")
    except Exception:
        # Routers appear from BE-03 onward; scaffold stays bootable meanwhile.
        pass


app = create_app()
