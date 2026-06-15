"""Pricing endpoints: current + SSE stream."""
from __future__ import annotations

import json


def test_current_price(client, alice_auth):
    r = client.get("/v1/pricing/AAPL", headers=alice_auth)
    assert r.status_code == 200
    body = r.json()
    assert body["ticker"] == "AAPL"
    assert body["price"] > 0


def test_current_price_unknown_404(client, alice_auth):
    assert client.get("/v1/pricing/ZZZ", headers=alice_auth).status_code == 404


def test_stream_emits_events(client, alice_auth):
    # Five ticks at the minimum interval; total well under the test deadline.
    r = client.get(
        "/v1/pricing/AAPL/stream?ticks=5&interval_ms=10",
        headers=alice_auth,
    )
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/event-stream")
    # SSE framing: events separated by a blank line; each starts `data: `.
    events = [chunk for chunk in r.text.strip().split("\n\n") if chunk]
    assert len(events) == 5
    payloads = [json.loads(e.removeprefix("data: ")) for e in events]
    assert all(p["ticker"] == "AAPL" for p in payloads)
    assert [p["tick"] for p in payloads] == [0, 1, 2, 3, 4]
