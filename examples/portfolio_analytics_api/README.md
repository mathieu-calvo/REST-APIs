# Portfolio Analytics API — Capstone

A complete FastAPI service that wires every chapter of this curriculum into one app. Notebooks 01.01 → 08.04 teach concepts in isolation; this folder is what those concepts look like *together*.

## What's in the box

| Concern | Where it lives | Notebook |
| --- | --- | --- |
| Validation (Pydantic v2) | `models/` | 1.3 |
| Routing under `/v1` | `routers/` + `main.py` | 2.x |
| Async + SSE pricing stream | `routers/pricing.py` | 3.x |
| Dependency injection, repos | `deps.py`, `repositories/` | 4.x |
| OAuth2 password + JWT | `auth.py`, `routers/auth.py` | 5.1, 5.2 |
| CORS, rate limit | `main.py` (`slowapi`) | 5.3 |
| Domain errors + handlers | `errors.py` | 6.1 |
| Structured logging | `observability.py` (structlog) | 6.2 |
| `/metrics`, OTel tracing | `observability.py` | 6.3 |
| Test suite | `tests/` | 7.x |
| `lifespan` + app factory | `main.py` | 8.1 |
| Multi-stage Dockerfile, non-root | `Dockerfile`, `.dockerignore` | 8.2 |

## Layout

```
portfolio_analytics_api/
├── src/portfolio_api/
│   ├── main.py              # app factory + lifespan
│   ├── settings.py          # pydantic-settings
│   ├── deps.py              # DI providers
│   ├── auth.py              # OAuth2 + JWT
│   ├── errors.py            # exception handlers
│   ├── observability.py     # structlog + Prometheus + OTel
│   ├── models/              # Asset, Portfolio, Holding, User, Token
│   ├── repositories/        # AssetRepo / PortfolioRepo + impls
│   └── routers/
│       ├── auth.py          # POST /token, GET /me
│       ├── assets.py        # CRUD on the asset universe
│       ├── portfolios.py    # CRUD + nested /holdings
│       ├── pricing.py       # current price + SSE live ticks
│       └── analytics.py     # totals, allocation, weights
├── tests/                   # pytest suite, 34 tests
├── Dockerfile               # multi-stage, non-root, HEALTHCHECK
├── .dockerignore
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Run it locally

From this directory:

```bash
pip install -e .[test]            # installs the package and pytest
uvicorn portfolio_api.main:app --reload
```

Then open <http://localhost:8000/docs> for Swagger UI, or `<http://localhost:8000/redoc>` for ReDoc.

## Try the API

There are two demo users:

| Username | Password | Scopes |
| --- | --- | --- |
| `alice` | `alice-secret` | `portfolios:read`, `portfolios:write` |
| `bob` | `bob-secret` | `portfolios:read` |

```bash
# 1. Get a token (OAuth2 password grant)
TOKEN=$(curl -s -X POST -d "username=alice&password=alice-secret" \
  http://localhost:8000/v1/auth/token | jq -r .access_token)

# 2. Identify yourself
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/v1/auth/me

# 3. List the seeded asset universe
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/v1/assets

# 4. Build a portfolio
PID=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"growth","holdings":[{"ticker":"AAPL","quantity":10},{"ticker":"BND","quantity":50}]}' \
  http://localhost:8000/v1/portfolios | jq -r .id)

# 5. Compute analytics over it
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/v1/analytics/portfolios/$PID | jq

# 6. Subscribe to a live price feed (SSE — keep the connection open)
curl -N -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/v1/pricing/AAPL/stream?ticks=20&interval_ms=200"

# 7. Inspect Prometheus metrics
curl -s http://localhost:8000/metrics | head
```

## Tests

```bash
pip install -e .[test]
PYTHONPATH=src pytest
```

The suite (34 tests across `tests/`) covers happy + sad paths for every router, scope-based authorization, JWT audience / signature validation, ownership isolation between users, SSE framing, analytics math, lifespan-backed real-repo wiring, request-id propagation, and the `/metrics` surface.

## Configuration

Everything is configured via env vars (prefix `PORTFOLIO_`) — see `src/portfolio_api/settings.py`. The defaults work for local development.

| Variable | Default | Purpose |
| --- | --- | --- |
| `PORTFOLIO_ENVIRONMENT` | `dev` | `dev` / `staging` / `prod`; surfaced in logs and tracing resource attrs |
| `PORTFOLIO_LOG_LEVEL` | `info` | `debug` / `info` / `warning` / `error` |
| `PORTFOLIO_REPO_BACKEND` | `memory` | `memory` or `sqlite` — the latter persists assets between restarts |
| `PORTFOLIO_SQLITE_PATH` | `:memory:` | File path when `REPO_BACKEND=sqlite` |
| `PORTFOLIO_JWT_SECRET` | dev-only string | **Must** be overridden outside dev |
| `PORTFOLIO_ACCESS_TOKEN_TTL_SECONDS` | `3600` | JWT `exp` window |
| `PORTFOLIO_CORS_ORIGINS` | `["http://localhost:5173"]` | JSON list of allowed origins |
| `PORTFOLIO_RATE_LIMIT_PER_MINUTE` | `120` | slowapi default cap, per IP |
| `PORTFOLIO_ENABLE_OTEL` | `true` | Set to `false` to silence the console span exporter |

## Docker

```bash
docker build -t portfolio-api:dev .
docker run --rm -p 8000:8000 \
  -e PORTFOLIO_JWT_SECRET=$(openssl rand -hex 32) \
  portfolio-api:dev
```

The image is multi-stage (builder + slim runtime), runs as a non-root `app` user (UID 10001), and exposes a `HEALTHCHECK` that hits `/healthz`. See notebook 08.02 for the full anatomy.

## Where the seams are

This app is small, but every external boundary goes through a seam that a test or a new implementation can replace:

- **`AssetRepo` / `PortfolioRepo` Protocols** — swap in-memory for SQLite (`PORTFOLIO_REPO_BACKEND=sqlite`) without touching a router. Tests use `app.dependency_overrides[get_asset_repo]` for total isolation.
- **`get_settings`** — `lru_cache`-d provider; tests pass a custom `Settings` to `create_app(...)`.
- **`get_current_user`** — single dep that gates every protected route; mocking it out is one `dependency_overrides` line.
- **`structlog` configuration** — one place; processors live in `observability.py` and the request-id middleware feeds them via a `contextvars` token.

Adding a feature (e.g., margin tracking, currency conversion) starts at a model in `models/`, optionally extends a repo, and adds at most one router + a handful of tests. The framework will not fight you.
