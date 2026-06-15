"""Pricing endpoints: current price + SSE live ticks."""
from __future__ import annotations

import asyncio
import json
import random
from typing import Annotated, AsyncIterator

from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import StreamingResponse

from portfolio_api.auth import get_current_user
from portfolio_api.deps import AssetRepoDep
from portfolio_api.errors import NotFoundError

router = APIRouter(
    prefix="/pricing",
    tags=["pricing"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/{ticker}")
def current_price(
    ticker: Annotated[str, Path(pattern=r"^[A-Za-z.]{1,10}$")],
    repo: AssetRepoDep,
) -> dict:
    asset = repo.get(ticker)
    if asset is None:
        raise NotFoundError(f"asset {ticker.upper()!r} not found")
    return {"ticker": asset.ticker, "price": asset.price}


async def _tick_stream(ticker: str, base_price: float, count: int, interval_s: float) -> AsyncIterator[bytes]:
    """Emit `count` SSE events with a random-walk price.

    SSE framing: `data: <json>\\n\\n`. The double-newline is the event separator."""
    price = base_price
    for i in range(count):
        # Random walk: ±0.5% drift per tick.
        price = round(price * (1 + random.uniform(-0.005, 0.005)), 4)
        payload = {"ticker": ticker, "price": price, "tick": i}
        yield f"data: {json.dumps(payload)}\n\n".encode("utf-8")
        await asyncio.sleep(interval_s)


@router.get(
    "/{ticker}/stream",
    response_class=StreamingResponse,
    summary="Server-Sent Events stream of simulated price ticks",
)
def stream_prices(
    ticker: Annotated[str, Path(pattern=r"^[A-Za-z.]{1,10}$")],
    repo: AssetRepoDep,
    ticks: Annotated[int, Query(ge=1, le=100, description="How many ticks to emit before closing")] = 10,
    interval_ms: Annotated[int, Query(ge=10, le=5000)] = 200,
) -> StreamingResponse:
    asset = repo.get(ticker)
    if asset is None:
        raise NotFoundError(f"asset {ticker.upper()!r} not found")
    return StreamingResponse(
        _tick_stream(asset.ticker, asset.price, ticks, interval_ms / 1000.0),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
