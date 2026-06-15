"""Lifespan + health endpoints."""
from __future__ import annotations

from fastapi.testclient import TestClient

from portfolio_api.main import create_app
from portfolio_api.settings import Settings


def test_lifespan_opens_and_closes_repos():
    """Without dependency overrides, the lifespan should produce a working AssetRepo."""
    settings = Settings(enable_otel=False, log_level="warning")
    app = create_app(settings)
    with TestClient(app) as c:
        # The repo dep pulls from app.state.asset_repo — populated by the lifespan.
        r = c.get("/healthz")
        assert r.status_code == 200
        # Without a token this would 401 — confirms the auth dep is wired.
        assert c.get("/v1/assets").status_code == 401

        # Mint a token and hit the real (non-overridden) repo.
        tok = c.post(
            "/v1/auth/token", data={"username": "alice", "password": "alice-secret"}
        ).json()["access_token"]
        r = c.get("/v1/assets", headers={"Authorization": f"Bearer {tok}"})
        assert r.status_code == 200
        tickers = {a["ticker"] for a in r.json()}
        assert "AAPL" in tickers  # SEED loaded


def test_readyz(client):
    assert client.get("/readyz").json() == {"status": "ready"}


def test_request_id_header(client):
    r = client.get("/healthz")
    assert "x-request-id" in {k.lower() for k in r.headers}


def test_request_id_propagates_when_supplied(client):
    r = client.get("/healthz", headers={"X-Request-ID": "test-rid-123"})
    assert r.headers.get("X-Request-ID") == "test-rid-123"


def test_metrics_endpoint(client):
    # Exercise at least one route first so counters are non-zero.
    client.get("/healthz")
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "http_requests_total" in r.text or "http_request_duration" in r.text
