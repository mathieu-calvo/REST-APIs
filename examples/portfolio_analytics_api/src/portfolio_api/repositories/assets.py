"""AssetRepo Protocol + in-memory and SQLite implementations — mirrors notebook 4.2."""
from __future__ import annotations

import sqlite3
import threading
from typing import Iterable, Protocol

from portfolio_api.models.assets import Asset, AssetClass

SEED: list[Asset] = [
    Asset(ticker="AAPL", name="Apple Inc.",        price=190.0, asset_class=AssetClass.EQUITY),
    Asset(ticker="MSFT", name="Microsoft",         price=420.0, asset_class=AssetClass.EQUITY),
    Asset(ticker="NVDA", name="NVIDIA Corp.",      price=900.0, asset_class=AssetClass.EQUITY),
    Asset(ticker="TSLA", name="Tesla Inc.",        price=250.0, asset_class=AssetClass.EQUITY),
    Asset(ticker="BND",  name="Vanguard Total Bond", price=72.50, asset_class=AssetClass.BOND),
]


class AssetRepo(Protocol):
    def get(self, ticker: str) -> Asset | None: ...
    def list(self) -> list[Asset]: ...
    def add(self, asset: Asset) -> Asset: ...
    def update_price(self, ticker: str, price: float) -> Asset | None: ...
    def delete(self, ticker: str) -> bool: ...


class InMemoryAssetRepo:
    """Dict-backed repo. Seeded on construction; threadsafe enough for the demo
    workload — a real concurrent app would back this with a proper store."""

    def __init__(self, seed: Iterable[Asset] | None = None) -> None:
        self._lock = threading.RLock()
        self._store: dict[str, Asset] = {a.ticker: a for a in (seed if seed is not None else SEED)}

    def get(self, ticker: str) -> Asset | None:
        with self._lock:
            return self._store.get(ticker.upper())

    def list(self) -> list[Asset]:
        with self._lock:
            return sorted(self._store.values(), key=lambda a: a.ticker)

    def add(self, asset: Asset) -> Asset:
        with self._lock:
            self._store[asset.ticker] = asset
            return asset

    def update_price(self, ticker: str, price: float) -> Asset | None:
        with self._lock:
            existing = self._store.get(ticker.upper())
            if existing is None:
                return None
            updated = existing.model_copy(update={"price": price})
            self._store[updated.ticker] = updated
            return updated

    def delete(self, ticker: str) -> bool:
        with self._lock:
            return self._store.pop(ticker.upper(), None) is not None


class SQLiteAssetRepo:
    """SQLite-backed AssetRepo — same Protocol contract, persisted bytes.

    Notebook 4.2 walked through this exact shape. The capstone uses it when
    `PORTFOLIO_REPO_BACKEND=sqlite` is set; tests stay on InMemory."""

    def __init__(self, db_path: str = ":memory:", seed: Iterable[Asset] | None = None) -> None:
        # check_same_thread=False because uvicorn workers route requests across
        # an internal threadpool. SQLite's connection lock plus our threading.RLock
        # in InMemoryAssetRepo are the two patterns to know.
        self._conn = sqlite3.connect(db_path, check_same_thread=False, isolation_level=None)
        self._lock = threading.RLock()
        self._init_schema()
        if seed is not None:
            for asset in seed:
                self.add(asset)
        elif self._is_empty():
            for asset in SEED:
                self.add(asset)

    def _init_schema(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS assets (
                ticker      TEXT PRIMARY KEY,
                name        TEXT NOT NULL,
                price       REAL NOT NULL,
                asset_class TEXT NOT NULL
            );
            """
        )

    def _is_empty(self) -> bool:
        cur = self._conn.execute("SELECT COUNT(*) FROM assets")
        return cur.fetchone()[0] == 0

    def _row_to_asset(self, row: tuple) -> Asset:
        ticker, name, price, asset_class = row
        return Asset(ticker=ticker, name=name, price=price, asset_class=AssetClass(asset_class))

    def get(self, ticker: str) -> Asset | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT ticker, name, price, asset_class FROM assets WHERE ticker = ?",
                (ticker.upper(),),
            ).fetchone()
            return self._row_to_asset(row) if row else None

    def list(self) -> list[Asset]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT ticker, name, price, asset_class FROM assets ORDER BY ticker"
            ).fetchall()
            return [self._row_to_asset(r) for r in rows]

    def add(self, asset: Asset) -> Asset:
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO assets (ticker, name, price, asset_class) VALUES (?,?,?,?)",
                (asset.ticker, asset.name, asset.price, asset.asset_class.value),
            )
            return asset

    def update_price(self, ticker: str, price: float) -> Asset | None:
        with self._lock:
            cur = self._conn.execute(
                "UPDATE assets SET price = ? WHERE ticker = ?",
                (price, ticker.upper()),
            )
            if cur.rowcount == 0:
                return None
            return self.get(ticker)

    def delete(self, ticker: str) -> bool:
        with self._lock:
            cur = self._conn.execute("DELETE FROM assets WHERE ticker = ?", (ticker.upper(),))
            return cur.rowcount > 0

    def close(self) -> None:
        self._conn.close()
