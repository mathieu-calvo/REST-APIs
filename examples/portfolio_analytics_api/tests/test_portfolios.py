"""Portfolio CRUD + holdings."""
from __future__ import annotations


def test_create_and_list(client, alice_auth):
    r = client.post(
        "/v1/portfolios",
        headers=alice_auth,
        json={"name": "growth", "holdings": [{"ticker": "AAPL", "quantity": 5}]},
    )
    assert r.status_code == 201, r.text
    pid = r.json()["id"]

    listed = client.get("/v1/portfolios", headers=alice_auth).json()
    assert any(p["id"] == pid for p in listed)
    assert all(p["owner"] == "alice" for p in listed)


def test_cannot_create_with_unknown_ticker(client, alice_auth):
    r = client.post(
        "/v1/portfolios",
        headers=alice_auth,
        json={"name": "bad", "holdings": [{"ticker": "ZZZ", "quantity": 1}]},
    )
    assert r.status_code == 409


def test_isolation_between_users(client, alice_auth, bob_auth):
    # Alice creates a portfolio.
    r = client.post("/v1/portfolios", headers=alice_auth, json={"name": "private"})
    pid = r.json()["id"]

    # Bob cannot see it in his list...
    bob_list = client.get("/v1/portfolios", headers=bob_auth).json()
    assert not any(p["id"] == pid for p in bob_list)

    # ...nor fetch it by ID (404, not 403, to avoid leaking existence).
    assert client.get(f"/v1/portfolios/{pid}", headers=bob_auth).status_code == 404


def test_add_and_remove_holding(client, alice_auth):
    pid = client.post("/v1/portfolios", headers=alice_auth, json={"name": "x"}).json()["id"]
    r = client.post(
        f"/v1/portfolios/{pid}/holdings",
        headers=alice_auth,
        json={"ticker": "MSFT", "quantity": 3},
    )
    assert r.status_code == 201
    assert any(h["ticker"] == "MSFT" for h in r.json()["holdings"])

    r = client.delete(f"/v1/portfolios/{pid}/holdings/MSFT", headers=alice_auth)
    assert r.status_code == 200
    assert all(h["ticker"] != "MSFT" for h in r.json()["holdings"])


def test_remove_holding_404_if_absent(client, alice_auth):
    pid = client.post("/v1/portfolios", headers=alice_auth, json={"name": "x"}).json()["id"]
    r = client.delete(f"/v1/portfolios/{pid}/holdings/NVDA", headers=alice_auth)
    assert r.status_code == 404


def test_add_holding_merges_same_ticker(client, alice_auth):
    pid = client.post(
        "/v1/portfolios",
        headers=alice_auth,
        json={"name": "acc", "holdings": [{"ticker": "AAPL", "quantity": 2}]},
    ).json()["id"]

    r = client.post(
        f"/v1/portfolios/{pid}/holdings",
        headers=alice_auth,
        json={"ticker": "AAPL", "quantity": 3},
    )
    aapl = [h for h in r.json()["holdings"] if h["ticker"] == "AAPL"]
    assert len(aapl) == 1
    assert aapl[0]["quantity"] == 5


def test_delete_portfolio(client, alice_auth):
    pid = client.post("/v1/portfolios", headers=alice_auth, json={"name": "to-del"}).json()["id"]
    assert client.delete(f"/v1/portfolios/{pid}", headers=alice_auth).status_code == 204
    assert client.get(f"/v1/portfolios/{pid}", headers=alice_auth).status_code == 404
