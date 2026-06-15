"""Structured logging, Prometheus metrics, OpenTelemetry — mirrors notebooks 6.2 & 6.3."""
from __future__ import annotations

import logging
import time
import uuid
from contextvars import ContextVar
from typing import Awaitable, Callable

import structlog
from fastapi import FastAPI, Request, Response
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.middleware.base import BaseHTTPMiddleware

from portfolio_api.settings import Settings

REQUEST_ID: ContextVar[str] = ContextVar("request_id", default="-")


def _request_id_processor(logger, method_name, event_dict):
    event_dict["request_id"] = REQUEST_ID.get()
    return event_dict


def configure_logging(settings: Settings) -> None:
    """Wire structlog + stdlib logging to emit one JSON line per event."""
    logging.basicConfig(
        format="%(message)s",
        level=settings.log_level.upper(),
        force=True,
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            _request_id_processor,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name) if name else structlog.get_logger()


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Attach a request id to every request, propagate via contextvar and header."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        rid = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        token = REQUEST_ID.set(rid)
        log = get_logger("http")
        t0 = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            log.exception(
                "request_failed",
                method=request.method,
                path=request.url.path,
                duration_ms=round((time.perf_counter() - t0) * 1000, 2),
            )
            REQUEST_ID.reset(token)
            raise
        response.headers["X-Request-ID"] = rid
        log.info(
            "request",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round((time.perf_counter() - t0) * 1000, 2),
        )
        REQUEST_ID.reset(token)
        return response


def install_metrics(app: FastAPI) -> None:
    """/metrics endpoint with per-route latency histograms."""
    Instrumentator(
        should_group_status_codes=True,
        excluded_handlers=["/metrics", "/healthz"],
    ).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)


def install_tracing(app: FastAPI, settings: Settings) -> None:
    """OpenTelemetry FastAPI instrumentation with a console exporter.

    A real deployment would swap ConsoleSpanExporter for an OTLP exporter
    pointed at the collector. The shape is identical."""
    if not settings.enable_otel:
        return
    from opentelemetry import trace
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (
        BatchSpanProcessor,
        ConsoleSpanExporter,
    )

    resource = Resource.create(
        {"service.name": settings.app_name, "deployment.environment": settings.environment}
    )
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app)
