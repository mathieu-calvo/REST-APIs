# REST APIs: FastAPI, Production Patterns, and Beyond

A hands-on tour of building REST APIs that hold up in production — FastAPI with Pydantic validation, dependency injection, async done right, authentication, observability, testing, and a comparison to Flask and gRPC. Every notebook runs the API in-process with `TestClient` (no servers to spin up), except the deployment chapter which intentionally launches a real Uvicorn server.

## Who This Is For

- Engineers building HTTP APIs and wanting the modern Python toolkit
- Data engineers serving models, datasets, or analytics over the wire
- Interview candidates revising API design, async Python, and auth patterns
- Anyone building a portfolio that demonstrates production-grade API craft

## Prerequisites

- Python 3.10+
- Comfort with Pydantic / dataclasses (or see `Pythonic-Skills/03_data_models/`)
- A working `pip` and virtual-env setup

## Setup

```bash
git clone https://github.com/mathieu-calvo/REST-APIs.git
cd REST-APIs
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Most notebooks run end-to-end with `TestClient` — no separate server. The deployment chapter (`08_deployment_and_beyond/01_uvicorn_workers_and_lifecycle.ipynb`) launches a real Uvicorn process and has terminal instructions inline.

## Repository Structure

```
REST-APIs/
├── 01_rest_foundations/
│   ├── 01_http_rest_status_codes.ipynb
│   ├── 02_first_fastapi_app.ipynb
│   └── 03_pydantic_request_response_validation.ipynb
├── 02_routing_and_resources/
│   ├── 01_path_and_query_params.ipynb
│   ├── 02_request_bodies_and_responses.ipynb
│   └── 03_routers_and_url_versioning.ipynb
├── 03_async_and_performance/
│   ├── 01_sync_vs_async_endpoints.ipynb
│   ├── 02_dont_block_the_event_loop.ipynb
│   └── 03_background_tasks_and_streaming.ipynb
├── 04_dependency_injection/
│   ├── 01_di_basics.ipynb
│   ├── 02_repository_swappable_data_sources.ipynb
│   └── 03_settings_and_config_with_pydantic.ipynb
├── 05_auth_and_security/
│   ├── 01_bearer_tokens_and_oauth2.ipynb
│   ├── 02_jwt_validation.ipynb
│   └── 03_cors_csrf_and_rate_limiting.ipynb
├── 06_errors_logging_observability/
│   ├── 01_http_exceptions_and_handlers.ipynb
│   ├── 02_structured_logging.ipynb
│   └── 03_metrics_and_tracing.ipynb
├── 07_testing/
│   ├── 01_testclient_sync.ipynb
│   ├── 02_async_httpx_asyncclient.ipynb
│   └── 03_fakes_and_dependency_overrides.ipynb
├── 08_deployment_and_beyond/
│   ├── 01_uvicorn_workers_and_lifecycle.ipynb
│   ├── 02_dockerizing_an_api.ipynb
│   ├── 03_flask_side_by_side.ipynb
│   └── 04_grpc_when_and_why.ipynb
├── examples/
│   └── portfolio_analytics_api/   # capstone — combines everything
├── requirements.txt
├── LICENSE
├── README.md
└── .gitignore
```

---

## Learning Path

### 1. REST Foundations (`01_rest_foundations/`)

What REST actually is, how FastAPI builds on it, and how Pydantic protects the boundary.

| Notebook | Topics |
|----------|--------|
| [01 - HTTP, REST, and Status Codes](01_rest_foundations/01_http_rest_status_codes.ipynb) | HTTP methods, status codes, idempotency, REST constraints |
| [02 - Your First FastAPI App](01_rest_foundations/02_first_fastapi_app.ipynb) | FastAPI app, endpoints, TestClient, OpenAPI / Swagger UI |
| [03 - Pydantic Request / Response Validation](01_rest_foundations/03_pydantic_request_response_validation.ipynb) | Request/response models, `Field()` constraints, validators, 422 handling |

### 2. Routing & Resources (`02_routing_and_resources/`)

Path and query parameters, request bodies, routers, and URL versioning.

| Notebook | Topics |
|----------|--------|
| [01 - Path and Query Parameters](02_routing_and_resources/01_path_and_query_params.ipynb) | Path and query params, `Query`/`Path` metadata, enum constraints |
| [02 - Request Bodies and Responses](02_routing_and_resources/02_request_bodies_and_responses.ipynb) | Request bodies, `response_model`, exclude_unset, raw `Response` |
| [03 - Routers and URL Versioning](02_routing_and_resources/03_routers_and_url_versioning.ipynb) | `APIRouter`, URL prefixes, versioning, router-level defaults |

### 3. Async & Performance (`03_async_and_performance/`)

When `async def` helps, when it hurts, and how to keep the event loop unblocked.

| Notebook | Topics |
|----------|--------|
| [01 - Sync vs Async Endpoints](03_async_and_performance/01_sync_vs_async_endpoints.ipynb) | Sync vs async endpoints, threadpool scheduling, latency benchmarking |
| [02 - Don't Block the Event Loop](03_async_and_performance/02_dont_block_the_event_loop.ipynb) | Blocking-call bug, `anyio.to_thread.run_sync`, process pools |
| [03 - Background Tasks and Streaming](03_async_and_performance/03_background_tasks_and_streaming.ipynb) | `BackgroundTasks`, `StreamingResponse`, SSE, when to use a queue |

### 4. Dependency Injection (`04_dependency_injection/`)

FastAPI's killer feature: typed, composable, testable dependencies.

| Notebook | Topics |
|----------|--------|
| [01 - Dependency Injection Basics](04_dependency_injection/01_di_basics.ipynb) | `Depends`, dep chains, class-based deps, caching, `yield` cleanup |
| [02 - Repository: Swappable Data Sources](04_dependency_injection/02_repository_swappable_data_sources.ipynb) | Repository protocol, in-memory + SQLite backends, dependency overrides |
| [03 - Settings and Config with Pydantic](04_dependency_injection/03_settings_and_config_with_pydantic.ipynb) | `BaseSettings`, `.env`, settings injection, startup validation |

### 5. Auth & Security (`05_auth_and_security/`)

Bearer tokens, OAuth2, JWT validation, and the security middleware every public API needs.

| Notebook | Topics |
|----------|--------|
| [01 - Bearer Tokens and OAuth2](05_auth_and_security/01_bearer_tokens_and_oauth2.ipynb) | HTTP Bearer, `OAuth2PasswordBearer`, token issuance and validation |
| [02 - JWT Validation](05_auth_and_security/02_jwt_validation.ipynb) | JWT structure, signing, claim validation, identity propagation |
| [03 - CORS, CSRF, and Rate Limiting](05_auth_and_security/03_cors_csrf_and_rate_limiting.ipynb) | `CORSMiddleware`, CSRF basics, `slowapi`, per-route rate limits |

### 6. Errors, Logging, Observability (`06_errors_logging_observability/`)

Crash gracefully, log with structure, and emit metrics + traces.

| Notebook | Topics |
|----------|--------|
| [01 - HTTPExceptions and Exception Handlers](06_errors_logging_observability/01_http_exceptions_and_handlers.ipynb) | `HTTPException`, custom handlers, consistent error shape |
| [02 - Structured Logging](06_errors_logging_observability/02_structured_logging.ipynb) | `structlog`, request IDs, log levels, stdout logging |
| [03 - Metrics and Tracing](06_errors_logging_observability/03_metrics_and_tracing.ipynb) | Prometheus metrics, auto-instrumentation, OpenTelemetry tracing |

### 7. Testing (`07_testing/`)

TestClient, async tests, and dependency overrides for fast, isolated test suites.

| Notebook | Topics |
|----------|--------|
| [01 - TestClient (sync)](07_testing/01_testclient_sync.ipynb) | `TestClient`, fixtures, assertions, pytest markers |
| [02 - Async Tests with httpx.AsyncClient](07_testing/02_async_httpx_asyncclient.ipynb) | `httpx.AsyncClient`, `pytest-asyncio`, async fixtures |
| [03 - Fakes and Dependency Overrides](07_testing/03_fakes_and_dependency_overrides.ipynb) | `dependency_overrides`, in-memory fakes, test isolation |

### 8. Deployment & Beyond (`08_deployment_and_beyond/`)

Uvicorn workers, Docker, Flask comparison, and gRPC for when REST isn't the right tool.

| Notebook | Topics |
|----------|--------|
| [01 - Uvicorn, Workers, and App Lifecycle](08_deployment_and_beyond/01_uvicorn_workers_and_lifecycle.ipynb) | Uvicorn CLI, workers, `lifespan`, reload vs production settings |
| [02 - Dockerizing an API](08_deployment_and_beyond/02_dockerizing_an_api.ipynb) | Multi-stage Dockerfile, non-root user, healthchecks, `.dockerignore` |
| [03 - Flask: Side-by-Side Comparison](08_deployment_and_beyond/03_flask_side_by_side.ipynb) | Flask vs FastAPI, validation/docs differences, migration sketch |
| [04 - gRPC: When and Why](08_deployment_and_beyond/04_grpc_when_and_why.ipynb) | Protobuf definitions, generated stubs, gRPC vs REST tradeoffs, streaming |

### Capstone: `examples/portfolio_analytics_api/`

A complete multi-router FastAPI app combining routing, dependency injection, auth, observability, and tests. Read its `README.md` to see how each notebook's lessons compose into a real service.

---

## Key Concepts Covered

| Concept | Where |
|---------|-------|
| Pydantic at the boundary | Foundations 03 |
| Async endpoints (when they help) | Async 01, Async 02 |
| Dependency injection | DI 01-03 |
| Repository pattern in an API | DI 02 |
| Auth: Bearer + JWT | Auth 01-02 |
| Observability (logs/metrics/traces) | Observability 02-03 |
| Testing with overrides | Testing 03 |
| Real deployment (uvicorn + Docker) | Deployment 01-02 |
| gRPC as an alternative | Deployment 04 |

## References

- FastAPI Documentation. https://fastapi.tiangolo.com
- Pydantic v2 Documentation. https://docs.pydantic.dev
- Starlette Documentation. https://www.starlette.io
- Fielding, R. T. (2000). *Architectural Styles and the Design of Network-Based Software Architectures* (Ph.D. dissertation).
- Newman, S. (2021). *Building Microservices* (2nd ed.). O'Reilly.
- Bellemare, A. (2020). *Building Event-Driven Microservices*. O'Reilly.

## License

MIT License. See [LICENSE](LICENSE) for details.
