# Portfolio Analytics API — Capstone

A complete FastAPI service that pulls together everything taught in this repo:

- **Resources**: `/v1/prices`, `/v1/portfolios`, `/v1/analytics`
- **Routing**: split into `APIRouter`s, mounted under `/v1`
- **Validation**: Pydantic request/response models with field validators
- **Dependency injection**: a `PriceRepo` Protocol with in-memory and SQLite backends, injected via `Depends`
- **Auth**: HTTP Bearer + JWT validation
- **Observability**: structured logging with `structlog`, `/metrics` Prometheus endpoint, OpenTelemetry traces
- **Testing**: a full `pytest` suite using `TestClient` and `dependency_overrides`
- **Deployment**: production-grade `Dockerfile` (multi-stage, non-root) and a `lifespan` for startup/shutdown

Run it locally:

```bash
uvicorn portfolio_analytics_api.main:app --reload
```

Open <http://localhost:8000/docs> to explore.

**This folder will be filled in during Phase 3 of the build.** It's a deliberate capstone — the
notebooks teach each concept in isolation, and this app shows the concepts working together.
