"""Portfolio analytics."""
from __future__ import annotations

import math


def test_analytics_full_round_trip(client, alice_auth):
    # Build a portfolio with mixed asset classes so allocation has multiple buckets.
    pid = client.post(
        "/v1/portfolios",
        headers=alice_auth,
        json={
            "name": "mixed",
            "holdings": [
                {"ticker": "AAPL", "quantity": 10},   # 10 * 190 = 1900
                {"ticker": "MSFT", "quantity": 5},    # 5  * 420 = 2100
                {"ticker": "BND",  "quantity": 100},  # 100 * 72.50 = 7250
            ],
        },
    ).json()["id"]

    r = client.get(f"/v1/analytics/portfolios/{pid}", headers=alice_auth)
    assert r.status_code == 200, r.text
    body = r.json()

    assert body["portfolio_id"] == pid
    assert math.isclose(body["total_value"], 1900 + 2100 + 7250, rel_tol=1e-6)

    # Weights must sum to 1.
    weight_sum = sum(h["weight"] for h in body["holdings"])
    assert math.isclose(weight_sum, 1.0, abs_tol=1e-4)

    # by_class: equity = 1900 + 2100 = 4000; bond = 7250.
    by_class = {row["asset_class"]: row for row in body["by_class"]}
    assert math.isclose(by_class["equity"]["market_value"], 4000, rel_tol=1e-6)
    assert math.isclose(by_class["bond"]["market_value"], 7250, rel_tol=1e-6)
    assert math.isclose(by_class["equity"]["weight"] + by_class["bond"]["weight"], 1.0, abs_tol=1e-4)


def test_analytics_empty_portfolio(client, alice_auth):
    pid = client.post("/v1/portfolios", headers=alice_auth, json={"name": "empty"}).json()["id"]
    r = client.get(f"/v1/analytics/portfolios/{pid}", headers=alice_auth)
    assert r.status_code == 200
    body = r.json()
    assert body["total_value"] == 0.0
    assert body["holdings"] == []
    assert body["by_class"] == []


def test_analytics_other_user_404(client, alice_auth, bob_auth):
    pid = client.post("/v1/portfolios", headers=alice_auth, json={"name": "private"}).json()["id"]
    assert client.get(f"/v1/analytics/portfolios/{pid}", headers=bob_auth).status_code == 404
