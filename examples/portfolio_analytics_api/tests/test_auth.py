"""Auth: token issuance + protected route behavior."""
from __future__ import annotations


def test_token_happy_path(client):
    r = client.post("/v1/auth/token", data={"username": "alice", "password": "alice-secret"})
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] > 0
    assert len(body["access_token"].split(".")) == 3  # JWT = header.payload.sig


def test_token_bad_password_401(client):
    r = client.post("/v1/auth/token", data={"username": "alice", "password": "nope"})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "unauthenticated"


def test_protected_route_requires_token(client):
    assert client.get("/v1/assets").status_code == 401


def test_protected_route_with_token(client, alice_auth):
    r = client.get("/v1/assets", headers=alice_auth)
    assert r.status_code == 200


def test_me_returns_user(client, alice_auth):
    r = client.get("/v1/auth/me", headers=alice_auth)
    assert r.status_code == 200
    assert r.json()["username"] == "alice"


def test_read_only_user_blocked_from_write(client, bob_auth):
    # Bob lacks portfolios:write scope.
    r = client.post(
        "/v1/assets",
        headers=bob_auth,
        json={"ticker": "ZZZ", "name": "Zed", "price": 1.0},
    )
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "forbidden"


def test_token_with_wrong_audience_rejected(client, settings):
    # Mint a token with a deliberately wrong audience and verify decode fails.
    from jose import jwt
    bad = jwt.encode(
        {
            "sub": "alice",
            "scopes": ["portfolios:read"],
            "iss": settings.jwt_issuer,
            "aud": "wrong-audience",
            "exp": 9_999_999_999,
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    r = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {bad}"})
    assert r.status_code == 401
