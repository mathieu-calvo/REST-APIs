"""Shared pytest fixtures — mirrors the patterns from notebook 7.3."""
from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from portfolio_api.deps import get_asset_repo, get_portfolio_repo
from portfolio_api.main import create_app
from portfolio_api.repositories.assets import InMemoryAssetRepo
from portfolio_api.repositories.portfolios import InMemoryPortfolioRepo
from portfolio_api.settings import Settings


@pytest.fixture
def settings() -> Settings:
    # Fresh settings per test, with OTel off so the noisy console exporter
    # doesn't pollute test output.
    return Settings(
        environment="dev",
        log_level="warning",
        enable_otel=False,
        jwt_secret="test-secret",
        rate_limit_per_minute=10_000,
    )


@pytest.fixture
def asset_repo() -> InMemoryAssetRepo:
    return InMemoryAssetRepo()


@pytest.fixture
def portfolio_repo() -> InMemoryPortfolioRepo:
    return InMemoryPortfolioRepo()


@pytest.fixture
def app(
    settings: Settings,
    asset_repo: InMemoryAssetRepo,
    portfolio_repo: InMemoryPortfolioRepo,
) -> FastAPI:
    """A fresh app per test, with repo deps overridden to use the per-test fakes."""
    app = create_app(settings)
    app.dependency_overrides[get_asset_repo] = lambda: asset_repo
    app.dependency_overrides[get_portfolio_repo] = lambda: portfolio_repo
    return app


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    # Context-manager form so the lifespan fires (notebook 7.3 + 8.1).
    with TestClient(app) as c:
        yield c


# --- auth helpers ------------------------------------------------------------

def _token_for(client: TestClient, username: str, password: str) -> str:
    r = client.post("/v1/auth/token", data={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture
def alice_auth(client: TestClient) -> dict[str, str]:
    """Headers for Alice (read+write scope)."""
    return {"Authorization": f"Bearer {_token_for(client, 'alice', 'alice-secret')}"}


@pytest.fixture
def bob_auth(client: TestClient) -> dict[str, str]:
    """Headers for Bob (read-only scope)."""
    return {"Authorization": f"Bearer {_token_for(client, 'bob', 'bob-secret')}"}
