# syntax=docker/dockerfile:1.7
# Multi-stage build matching the shape taught in notebook 08.02.

# ----- stage 1: builder ------------------------------------------------------
FROM python:3.12.7-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /build
COPY requirements.txt .
RUN pip install -r requirements.txt

# Install the package itself so `portfolio_api` imports cleanly at runtime.
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-deps .

# ----- stage 2: runtime ------------------------------------------------------
FROM python:3.12.7-slim-bookworm AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    PORTFOLIO_LOG_LEVEL=info

RUN groupadd --system --gid 10001 app && \
    useradd  --system --uid 10001 --gid 10001 --home-dir /app --no-create-home app

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
USER app

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request,sys; \
sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2).status==200 else 1)"

EXPOSE 8000
CMD ["uvicorn", "portfolio_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
