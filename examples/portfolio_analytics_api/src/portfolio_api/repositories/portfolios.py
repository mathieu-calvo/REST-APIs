"""PortfolioRepo Protocol + in-memory implementation."""
from __future__ import annotations

import threading
from itertools import count
from typing import Protocol

from portfolio_api.models.portfolios import Holding, Portfolio


class PortfolioRepo(Protocol):
    def get(self, portfolio_id: int) -> Portfolio | None: ...
    def list_for_owner(self, owner: str) -> list[Portfolio]: ...
    def add(self, *, owner: str, name: str, holdings: list[Holding]) -> Portfolio: ...
    def add_holding(self, portfolio_id: int, holding: Holding) -> Portfolio | None: ...
    def remove_holding(self, portfolio_id: int, ticker: str) -> Portfolio | None: ...
    def delete(self, portfolio_id: int) -> bool: ...


class InMemoryPortfolioRepo:
    """Dict-backed PortfolioRepo. ID generator + lock keep mutations consistent
    under TestClient's threaded execution model and Uvicorn's per-worker thread pool."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._store: dict[int, Portfolio] = {}
        self._ids = count(start=1)

    def get(self, portfolio_id: int) -> Portfolio | None:
        with self._lock:
            return self._store.get(portfolio_id)

    def list_for_owner(self, owner: str) -> list[Portfolio]:
        with self._lock:
            return sorted(
                (p for p in self._store.values() if p.owner == owner),
                key=lambda p: p.id,
            )

    def add(self, *, owner: str, name: str, holdings: list[Holding]) -> Portfolio:
        with self._lock:
            pid = next(self._ids)
            p = Portfolio(id=pid, owner=owner, name=name, holdings=list(holdings))
            self._store[pid] = p
            return p

    def add_holding(self, portfolio_id: int, holding: Holding) -> Portfolio | None:
        with self._lock:
            existing = self._store.get(portfolio_id)
            if existing is None:
                return None
            # If the ticker is already in the portfolio, sum the quantity.
            merged: list[Holding] = []
            replaced = False
            for h in existing.holdings:
                if h.ticker == holding.ticker:
                    merged.append(Holding(ticker=h.ticker, quantity=h.quantity + holding.quantity))
                    replaced = True
                else:
                    merged.append(h)
            if not replaced:
                merged.append(holding)
            updated = existing.model_copy(update={"holdings": merged})
            self._store[portfolio_id] = updated
            return updated

    def remove_holding(self, portfolio_id: int, ticker: str) -> Portfolio | None:
        with self._lock:
            existing = self._store.get(portfolio_id)
            if existing is None:
                return None
            ticker = ticker.upper()
            new_holdings = [h for h in existing.holdings if h.ticker != ticker]
            if len(new_holdings) == len(existing.holdings):
                # Caller will see "no change" and may want to 404; signal via
                # returning the unchanged portfolio. Router decides.
                return existing
            updated = existing.model_copy(update={"holdings": new_holdings})
            self._store[portfolio_id] = updated
            return updated

    def delete(self, portfolio_id: int) -> bool:
        with self._lock:
            return self._store.pop(portfolio_id, None) is not None
