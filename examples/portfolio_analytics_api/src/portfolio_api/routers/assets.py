"""Asset CRUD — mirrors notebook 2.x routing patterns."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status

from portfolio_api.auth import get_current_user, require_scope
from portfolio_api.deps import AssetRepoDep
from portfolio_api.errors import ConflictError, NotFoundError
from portfolio_api.models.assets import Asset, AssetClass, AssetCreate
from portfolio_api.models.auth import User

router = APIRouter(
    prefix="/assets",
    tags=["assets"],
    dependencies=[Depends(get_current_user)],
)


@router.get("", response_model=list[Asset])
def list_assets(
    repo: AssetRepoDep,
    asset_class: Annotated[AssetClass | None, Query(description="Filter by asset class")] = None,
) -> list[Asset]:
    items = repo.list()
    if asset_class is not None:
        items = [a for a in items if a.asset_class == asset_class]
    return items


@router.get("/{ticker}", response_model=Asset)
def get_asset(
    repo: AssetRepoDep,
    ticker: Annotated[str, Path(pattern=r"^[A-Za-z.]{1,10}$")],
) -> Asset:
    asset = repo.get(ticker)
    if asset is None:
        raise NotFoundError(f"asset {ticker.upper()!r} not found")
    return asset


@router.post(
    "",
    response_model=Asset,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_scope("portfolios:write"))],
)
def create_asset(payload: AssetCreate, repo: AssetRepoDep) -> Asset:
    if repo.get(payload.ticker) is not None:
        raise ConflictError(f"asset {payload.ticker!r} already exists")
    return repo.add(Asset.model_validate(payload.model_dump()))


@router.patch(
    "/{ticker}/price",
    response_model=Asset,
    dependencies=[Depends(require_scope("portfolios:write"))],
)
def update_price(
    repo: AssetRepoDep,
    ticker: Annotated[str, Path(pattern=r"^[A-Za-z.]{1,10}$")],
    price: Annotated[float, Query(ge=0)],
) -> Asset:
    updated = repo.update_price(ticker, price)
    if updated is None:
        raise NotFoundError(f"asset {ticker.upper()!r} not found")
    return updated


@router.delete(
    "/{ticker}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_scope("portfolios:write"))],
)
def delete_asset(
    repo: AssetRepoDep,
    ticker: Annotated[str, Path(pattern=r"^[A-Za-z.]{1,10}$")],
    _user: Annotated[User, Depends(get_current_user)],
) -> None:
    if not repo.delete(ticker):
        raise NotFoundError(f"asset {ticker.upper()!r} not found")
