"""FastAPI application factory and ASGI entrypoint."""

from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.api.routers import auth, predictions, stats, system
from app.core.config import settings
from app.core.logging import configure_logging, get_logger, request_id_var
from app.db.base import Base
from app.db.session import AsyncSessionLocal, engine
from app.ml.predictor import get_predictor
from app.seed import seed_demo_user

logger = get_logger("app.main")


async def _init_models() -> None:
    """Create tables that don't exist yet (local-first convenience)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    configure_logging(level=settings.log_level, json_logs=settings.is_production)
    logger.info("startup", app=settings.app_name, environment=settings.environment)

    await _init_models()
    async with AsyncSessionLocal() as session:
        await seed_demo_user(session)

    # Warm up the model. Missing artifact is non-fatal so docs stay reachable.
    try:
        get_predictor().load()
    except FileNotFoundError as exc:
        logger.warning("model_not_loaded", error=str(exc))

    yield
    await engine.dispose()
    logger.info("shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description="Chest X-ray classification API (ResNet50, 4 classes).",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        rid = request.headers.get("X-Request-ID", uuid.uuid4().hex[:12])
        token = request_id_var.set(rid)
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("unhandled_error", path=request.url.path, method=request.method)
            request_id_var.reset(token)
            return JSONResponse(status_code=500, content={"detail": "Internal server error"})
        elapsed = (time.perf_counter() - start) * 1000.0
        response.headers["X-Request-ID"] = rid
        if request.url.path.startswith("/api"):
            logger.info(
                "request",
                method=request.method,
                path=request.url.path,
                status=response.status_code,
                duration_ms=round(elapsed, 2),
            )
        request_id_var.reset(token)
        return response

    # API routers
    app.include_router(system.router, prefix="/api")
    app.include_router(auth.router, prefix="/api")
    app.include_router(predictions.router, prefix="/api")
    app.include_router(stats.router, prefix="/api")

    # Local uploads (only meaningful when STORAGE_BACKEND=local)
    if settings.storage_backend.lower() == "local":
        media_dir = settings.resolve_path(settings.local_storage_dir)
        media_dir.mkdir(parents=True, exist_ok=True)
        app.mount("/media", StaticFiles(directory=str(media_dir)), name="media")

    # Serve the built SPA in production (frontend copied into app/static).
    static_dir = Path(settings.resolve_path("./app/static"))
    if static_dir.is_dir():
        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="spa")
    else:
        @app.get("/", tags=["system"])
        async def root() -> dict:
            return {"app": settings.app_name, "docs": "/api/docs"}

    return app


app = create_app()
