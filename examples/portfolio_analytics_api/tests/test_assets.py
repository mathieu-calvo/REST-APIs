"""Asset CRUD."""
from __future__ import annotations


def test_list_seeded_assets(client, alice_auth):
    r = client.get("/v1/assets", headers=alice_auth)
    assert r.status_code == 200
    tickers = {a["ticker"] for a in r.json()}
    assert {"AAPL", "MSFT", "NVDA", "TSLA", "BND"}.issubset(tickers)


def test_filter_by_asset_class(client, alice_auth):
    r = client.get("/v1/assets?asset_class=bond", headers=alice_auth)
    assert r.status_code == 200
    rows = r.json()
    assert all(a["asset_class"] == "bond" for a in rows)
    assert {a["ticker"] for a in rows} == {"BND"}


def test_get_single_asset(client, alice_auth):
    r = client.get("/v1/assets/AAPL", headers=alice_auth)
    assert r.status_code == 200
    assert r.json()["ticker"] == "AAPL"


def test_get_unknown_404(client, alice_auth):
    r = client.get("/v1/assets/ZZZ", headers=alice_auth)
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "not_found"


def test_create_then_get(client, alice_auth):
    payload = {"ticker": "GOOG", "name": "Alphabet", "price": 175.0, "asset_class": "equity"}
    r = client.post("/v1/assets", headers=alice_auth, json=payload)
    assert r.status_code == 201, r.text
    assert r.json()["ticker"] == "GOOG"
    assert client.get("/v1/assets/GOOG", headers=alice_auth).status_code == 200


def test_create_conflict(client, alice_auth):
    # AAPL is seeded.
    r = client.post(
        "/v1/assets",
        headers=alice_auth,
        json={"ticker": "AAPL", "name": "dup", "price": 1.0},
    )
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "conflict"


def test_create_validation_error(client, alice_auth):
    r = client.post(
        "/v1/assets",
        headers=alice_auth,
        json={"ticker": "lowercase", "name": "x", "price": -1},
    )
    # ticker passes the lowercase->upper validator, then fails the pattern
    # because the pattern is uppercase-only after the input transform.
    # The 'price' < 0 alone is enough to push it to 422.
    assert r.status_code == 422
    body = r.json()
    assert body["error"]["code"] == "validation_error"
    assert isinstance(body["error"]["details"], list)


def test_update_price(client, alice_auth):
    r = client.patch("/v1/assets/AAPL/price?price=200.0", headers=alice_auth)
    assert r.status_code == 200
    assert r.json()["price"] == 200.0


def test_delete_asset(client, alice_auth):
    assert client.delete("/v1/assets/TSLA", headers=alice_auth).status_code == 204
    assert client.get("/v1/assets/TSLA", headers=alice_auth).status_code == 404
