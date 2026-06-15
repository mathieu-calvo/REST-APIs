"""Application factory + lifespan. Mirrors notebook 8.1's lifespan pattern."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from portfolio_api.errors import install_error_handlers
from portfolio_api.observability import (
    RequestIdMiddleware,
    configure_logging,
    get_logger,
    install_metrics,
    install_tracing,
)
from portfolio_api.repositories.assets import InMemoryAssetRepo, SQLiteAssetRepo
from portfolio_api.repositories.portfolios import InMemoryPortfolioRepo
from portfolio_api.routers import analytics, assets, auth, portfolios, pricing
from portfolio_api.settings import Settings, get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings: Settings = app.state.settings
    log = get_logger("lifespan")
    log.info("startup_begin", environment=settings.environment, repo=settings.repo_backend)

    if settings.repo_backend == "sqlite":
        app.state.asset_repo = SQLiteAssetRepo(db_path=settings.sqlite_path)
    else:
        app.state.asset_repo = InMemoryAssetRepo()
    app.state.portfolio_repo = InMemoryPortfolioRepo()

    log.info("startup_complete")
    yield

    log.info("shutdown_begin")
    repo = getattr(app.state, "asset_repo", None)
    if hasattr(repo, "close"):
        repo.close()
    log.info("shutdown_complete")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the FastAPI app. Pass a custom Settings for tests; otherwise
    pulls from the cached `get_settings()` (env-driven)."""
    settings = settings or get_settings()
    configure_logging(settings)

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description=(
            "Capstone for the REST-APIs curriculum — a complete FastAPI service "
            "that demonstrates every chapter working together: routing, validation, "
            "DI, auth, observability, testing, and deployment."
        ),
        lifespan=lifespan,
    )
    app.state.settings = settings

    limiter = Limiter(key_func=get_remote_address, default_limits=[f"{settings.rate_limit_per_minute}/minute"])
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestIdMiddleware)

    install_error_handlers(app)
    install_metrics(app)
    install_tracing(app, settings)

    # Public / unauthenticated endpoints first.
    @app.get("/healthz", tags=["health"], include_in_schema=False)
    def healthz():
        return {"status": "ok"}

    @app.get("/readyz", tags=["health"], include_in_schema=False)
    def readyz():
        # In a real app you'd ping the DB here.
        return {"status": "ready"}

    # Versioned routers.
    app.include_router(auth.router, prefix="/v1")
    app.include_router(assets.router, prefix="/v1")
    app.include_router(portfolios.router, prefix="/v1")
    app.include_router(pricing.router, prefix="/v1")
    app.include_router(analytics.router, prefix="/v1")

    return app


app = create_app()
