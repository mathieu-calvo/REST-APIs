"""Portfolio analytics: total value, allocation by class, per-ticker exposure."""
from __future__ import annotations

from collections import defaultdict
from typing import Annotated

from fastapi import APIRouter, Depends, Path
from pydantic import BaseModel, Field

from portfolio_api.auth import get_current_user
from portfolio_api.deps import AssetRepoDep, PortfolioRepoDep
from portfolio_api.errors import ConflictError, NotFoundError
from portfolio_api.models.assets import AssetClass
from portfolio_api.models.auth import User

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
    dependencies=[Depends(get_current_user)],
)


class HoldingValue(BaseModel):
    ticker: str
    quantity: float
    price: float
    market_value: float
    weight: float = Field(description="Fraction of total portfolio value, 0..1")


class AllocationByClass(BaseModel):
    asset_class: AssetClass
    market_value: float
    weight: float


class PortfolioAnalytics(BaseModel):
    portfolio_id: int
    portfolio_name: str
    total_value: float
    holdings: list[HoldingValue]
    by_class: list[AllocationByClass]


@router.get("/portfolios/{portfolio_id}", response_model=PortfolioAnalytics)
def portfolio_analytics(
    portfolio_id: Annotated[int, Path(ge=1)],
    portfolio_repo: PortfolioRepoDep,
    asset_repo: AssetRepoDep,
    user: Annotated[User, Depends(get_current_user)],
) -> PortfolioAnalytics:
    p = portfolio_repo.get(portfolio_id)
    if p is None or p.owner != user.username:
        raise NotFoundError(f"portfolio {portfolio_id} not found")

    enriched: list[tuple[str, float, float, float, AssetClass]] = []
    total = 0.0
    for h in p.holdings:
        asset = asset_repo.get(h.ticker)
        if asset is None:
            # Holdings should always point at known assets — this is a 409
            # because it's an inconsistency the caller can fix by removing the
            # orphan holding or re-adding the asset.
            raise ConflictError(f"holding references unknown asset {h.ticker!r}")
        mv = asset.price * h.quantity
        total += mv
        enriched.append((asset.ticker, h.quantity, asset.price, mv, asset.asset_class))

    holdings = [
        HoldingValue(
            ticker=t,
            quantity=q,
            price=pr,
            market_value=round(mv, 4),
            weight=round(mv / total, 6) if total > 0 else 0.0,
        )
        for (t, q, pr, mv, _) in enriched
    ]

    bucket: dict[AssetClass, float] = defaultdict(float)
    for _, _, _, mv, klass in enriched:
        bucket[klass] += mv
    by_class = [
        AllocationByClass(
            asset_class=k,
            market_value=round(v, 4),
            weight=round(v / total, 6) if total > 0 else 0.0,
        )
        for k, v in sorted(bucket.items(), key=lambda kv: kv[0].value)
    ]

    return PortfolioAnalytics(
        portfolio_id=p.id,
        portfolio_name=p.name,
        total_value=round(total, 4),
        holdings=holdings,
        by_class=by_class,
    )
