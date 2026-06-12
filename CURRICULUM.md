# Curriculum Plan

Tracking document for building out the REST-APIs notebooks. The repo currently has 25 stub notebooks (section headers only); this file is the master plan for filling them in.

## Conventions

- **Pydantic v2** with `pydantic-settings` for config.
- **Domain throughout**: portfolio / asset analytics. Core models reused chapter-to-chapter: `Asset(ticker, name, price)`, `Portfolio`, `Holding`.
- **In-process execution**: `TestClient` (or `httpx.AsyncClient` + `ASGITransport`) for every runnable cell except 08.01 (real Uvicorn) and 08.02 (Docker).
- **Notebook shape** (every notebook): opening objectives → scaffolded sections with prose + runnable code → key takeaways → 2-3 exercises → capstone tie-in line.
- **Depth**: tutorial-grade. Every code cell executes; learners can read top-to-bottom and run it.

## Progress

- [x] 01.01 HTTP, REST, Status Codes
- [x] 01.02 First FastAPI App
- [x] 01.03 Pydantic Request / Response Validation
- [x] 02.01 Path and Query Parameters
- [x] 02.02 Request Bodies and Responses
- [x] 02.03 Routers and URL Versioning
- [x] 03.01 Sync vs Async Endpoints
- [x] 03.02 Don't Block the Event Loop
- [x] 03.03 Background Tasks and Streaming
- [x] 04.01 DI Basics
- [x] 04.02 Repository: Swappable Data Sources
- [x] 04.03 Settings and Config with Pydantic
- [ ] 05.01 Bearer Tokens and OAuth2
- [ ] 05.02 JWT Validation
- [ ] 05.03 CORS, CSRF, and Rate Limiting
- [ ] 06.01 HTTPException and Handlers
- [ ] 06.02 Structured Logging
- [ ] 06.03 Metrics and Tracing
- [ ] 07.01 TestClient (sync)
- [ ] 07.02 Async Tests with httpx.AsyncClient
- [ ] 07.03 Fakes and Dependency Overrides
- [ ] 08.01 Uvicorn, Workers, Lifecycle
- [ ] 08.02 Dockerizing an API
- [ ] 08.03 Flask Side-by-Side
- [ ] 08.04 gRPC: When and Why
- [ ] Capstone: `examples/portfolio_analytics_api/`

---

## Chapter 1 — REST Foundations

### 1.1 HTTP, REST, Status Codes
**Goal**: ground the learner in HTTP and REST before any FastAPI code.
- Request/response cycle: `httpx.get("https://httpbin.org/get")`, inspect `Request`, `Response`, headers.
- Methods table: GET / POST / PUT / PATCH / DELETE — safe vs idempotent matrix.
- Status code families: live demo via `https://httpbin.org/status/{code}`.
- Idempotency demo: repeat a `PUT` vs a `POST` and reason about effects.
- REST constraints: statelessness, uniform interface, cacheability, layered system.
- URLs / resources / representations: content negotiation via `Accept`.
- Exercises: classify operations as safe/idempotent; pick correct status codes for given scenarios.
- Capstone tie-in: none — concepts only.

### 1.2 First FastAPI App
**Goal**: smallest possible FastAPI app, fully exercised.
- `app = FastAPI()` + `@app.get("/")`.
- Typed path and query params (foreshadow Ch 2).
- `TestClient` round-trip + assertions.
- OpenAPI / `/docs` / `/redoc` / `/openapi.json` inspection as a dict.
- `status_code=status.HTTP_201_CREATED` per route.
- `tags`, `summary`, `description` for docs grouping.
- Exercises: add a `/health` endpoint; modify `response_description`.
- Capstone tie-in: this app becomes the seed of `main.py`.

### 1.3 Pydantic Request / Response Validation
**Goal**: Pydantic v2 at the API boundary.
- `class Asset(BaseModel)` — `ticker`, `name`, `price`.
- `Field(min_length=1, ge=0, pattern=r"^[A-Z.]{1,10}$")`.
- Request body: `def create_asset(asset: Asset)`.
- `response_model=AssetOut` to strip internal fields.
- `@field_validator("ticker")` to uppercase.
- 422 error shape walkthrough; preview custom handler (full version in 6.1).
- Exercises: add a validated `Portfolio` model; force a 422 and inspect it.
- Capstone tie-in: this `Asset` schema is reused unchanged.

## Chapter 2 — Routing & Resources

### 2.1 Path and Query Parameters
- Path params: `{asset_id}`, typed.
- `Query(default=..., ge=1, le=100, alias="page-size")`.
- `Enum` constraint for `AssetClass = {"equity", "bond", "cash"}`.
- `Path(..., ge=1)` for numeric path validation.
- Exercises: filter by enum; paginate.

### 2.2 Request Bodies and Responses
- Multiple body params (`Body(...)` to disambiguate).
- `response_model_exclude_unset=True` for PATCH semantics.
- Raw `Response` for non-JSON (e.g., CSV export of holdings).
- Per-endpoint `status_code` and `responses=` schema.
- Exercises: implement PATCH that ignores omitted fields.

### 2.3 Routers and URL Versioning
- `APIRouter(prefix="/assets", tags=["assets"])`.
- Mount routers under `/v1`.
- Router-level `dependencies=` (e.g., shared auth).
- Versioning strategy: deprecation headers, parallel `/v2`.
- Exercises: split a monolithic app into two routers.

## Chapter 3 — Async & Performance

### 3.1 Sync vs Async Endpoints
- `def` vs `async def` — threadpool routing under the hood.
- Microbenchmark: 100 concurrent requests via `httpx.AsyncClient` against an in-process app.
- When async actually helps (I/O wait), when it doesn't (CPU).
- Exercises: convert a sync endpoint to async; measure.

### 3.2 Don't Block the Event Loop
- The `time.sleep(2)` inside `async def` disaster — observe latency explosion.
- Fix with `anyio.to_thread.run_sync` for sync libs.
- `ProcessPoolExecutor` for CPU-bound (price calc).
- Exercises: spot-the-bug exercise on three candidate snippets.

### 3.3 Background Tasks and Streaming
- `BackgroundTasks` param injection (e.g., post-create notification).
- `StreamingResponse` chunking a large CSV.
- SSE (`text/event-stream`) for live prices.
- When to graduate to a real queue (Celery / RQ / SQS).
- Exercises: build an SSE counter endpoint.

## Chapter 4 — Dependency Injection

### 4.1 DI Basics
- `Depends(get_settings)` — function dep.
- Class-callable deps (`class Pagination: def __init__(self, page=1, size=20)`).
- Per-request caching, dep chains.
- `yield` cleanup pattern.
- Exercises: build a `RequestContext` dep used by 3 routes.

### 4.2 Repository: Swappable Data Sources
- `class AssetRepo(Protocol)`.
- `InMemoryAssetRepo` (dict) + `SQLiteAssetRepo` (`sqlite3` stdlib).
- `app.dependency_overrides[get_repo] = lambda: InMemoryAssetRepo()` for tests.
- Exercises: add a `PostgresAssetRepo` skeleton.

### 4.3 Settings and Config with Pydantic
- `pydantic_settings.BaseSettings` with `.env`.
- `@lru_cache` settings provider.
- Fail-fast startup validation.
- Secrets handling: env > .env > defaults precedence.
- Exercises: add a per-env feature flag.

## Chapter 5 — Auth & Security

### 5.1 Bearer Tokens and OAuth2
- `HTTPBearer` scheme + 401 handling.
- `OAuth2PasswordBearer` + `/token` endpoint returning opaque token.
- `Depends(get_current_user)` propagation.
- Exercises: add a protected route; show 401 vs 403.

### 5.2 JWT Validation
- `python-jose` HS256 encode/decode.
- Claim validation: `exp`, `iss`, `aud`.
- Identity propagation through deps.
- Rotation / `kid` note.
- Exercises: write a token-expiry test.

### 5.3 CORS, CSRF, Rate Limiting
- `CORSMiddleware` strict origin list.
- CSRF + `SameSite=Lax` cookie strategy.
- `slowapi` per-route limits; bypass for `/health`.
- Exercises: simulate a rate-limit breach in TestClient.

## Chapter 6 — Errors, Logging, Observability

### 6.1 HTTPException and Handlers
- `raise HTTPException(status_code=404, detail=...)`.
- `@app.exception_handler(DomainError)` returning consistent `ErrorResponse`.
- Validation error customization.
- Exercises: unify two diverging error shapes.

### 6.2 Structured Logging
- `structlog` JSON renderer.
- Request-ID middleware + `contextvars` propagation.
- Log levels per environment.
- Exercises: add user-id to every log line.

### 6.3 Metrics and Tracing
- `prometheus-fastapi-instrumentator` → `/metrics`.
- OpenTelemetry tracer + console exporter (OTLP note).
- Trace-ID injection into structlog.
- Exercises: instrument a custom counter.

## Chapter 7 — Testing

### 7.1 TestClient (sync)
- Fixtures: `client`, `app`, sample data.
- `client.post(...).json()` assertions.
- Parametrized happy/sad paths.
- Exercises: write 3 tests for the `Asset` CRUD routes.

### 7.2 Async Tests with httpx.AsyncClient
- `pytest-asyncio` + `asyncio_mode = "auto"`.
- `AsyncClient(transport=ASGITransport(app=app))`.
- Async fixtures.
- Exercises: convert a sync test to async.

### 7.3 Fakes and Dependency Overrides
- Fake repo replacing SQLite per-test.
- `app.dependency_overrides` set/reset.
- Test isolation patterns.
- Exercises: build a fake clock for time-sensitive tests.

## Chapter 8 — Deployment & Beyond

### 8.1 Uvicorn, Workers, Lifecycle
**Note**: this notebook launches a real Uvicorn process. Inline terminal instructions.
- `uvicorn app:app --workers 4`.
- `reload` vs production.
- `@asynccontextmanager async def lifespan(app)` for startup/shutdown.
- Graceful shutdown semantics.

### 8.2 Dockerizing an API
- Multi-stage `Dockerfile`: builder → slim runtime.
- Non-root `USER`.
- `HEALTHCHECK` + readiness pattern.
- `.dockerignore` essentials.
- Exercises: shrink the image; add a build-arg.

### 8.3 Flask Side-by-Side
- Same `/assets` endpoint in Flask vs FastAPI.
- Manual `request.get_json()` + validation vs Pydantic.
- OpenAPI generation gap.
- Migration recipe.

### 8.4 gRPC: When and Why
- `assets.proto` definition.
- `grpc_tools.protoc` codegen → stubs.
- Unary + server-streaming RPC.
- Comparison table (typing, browser support, schema evolution, observability).

## Capstone — `examples/portfolio_analytics_api/`

Layout:

```
portfolio_analytics_api/
├── src/portfolio_api/
│   ├── main.py              # app factory + lifespan
│   ├── settings.py          # Ch 4.3
│   ├── deps.py              # Ch 4.1
│   ├── auth.py              # Ch 5.1-5.2
│   ├── observability.py     # Ch 6.2-6.3
│   ├── models/              # Ch 1.3
│   ├── repositories/        # Ch 4.2
│   └── routers/
│       ├── assets.py        # Ch 2
│       ├── portfolios.py
│       ├── holdings.py
│       └── pricing.py
├── tests/                   # Ch 7
├── Dockerfile               # Ch 8.2
└── README.md
```

Composition order: build it last, referencing each chapter inline ("the auth here is from 5.2").
