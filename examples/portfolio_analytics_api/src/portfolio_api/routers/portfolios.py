"""Portfolio CRUD + nested holdings."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path, status

from portfolio_api.auth import get_current_user, require_scope
from portfolio_api.deps import AssetRepoDep, PortfolioRepoDep
from portfolio_api.errors import ConflictError, NotFoundError
from portfolio_api.models.auth import User
from portfolio_api.models.portfolios import (
    Holding,
    HoldingCreate,
    Portfolio,
    PortfolioCreate,
)

router = APIRouter(
    prefix="/portfolios",
    tags=["portfolios"],
    dependencies=[Depends(get_current_user)],
)


def _check_tickers_exist(holdings: list[HoldingCreate], asset_repo) -> None:
    for h in holdings:
        if asset_repo.get(h.ticker) is None:
            raise ConflictError(f"unknown ticker in holdings: {h.ticker!r}")


@router.get("", response_model=list[Portfolio])
def list_portfolios(
    portfolio_repo: PortfolioRepoDep,
    user: Annotated[User, Depends(get_current_user)],
) -> list[Portfolio]:
    return portfolio_repo.list_for_owner(user.username)


@router.post(
    "",
    response_model=Portfolio,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_scope("portfolios:write"))],
)
def create_portfolio(
    payload: PortfolioCreate,
    portfolio_repo: PortfolioRepoDep,
    asset_repo: AssetRepoDep,
    user: Annotated[User, Depends(get_current_user)],
) -> Portfolio:
    _check_tickers_exist(payload.holdings, asset_repo)
    seeded = [Holding(ticker=h.ticker, quantity=h.quantity) for h in payload.holdings]
    return portfolio_repo.add(owner=user.username, name=payload.name, holdings=seeded)


def _get_or_404(portfolio_repo, portfolio_id: int, user: User) -> Portfolio:
    p = portfolio_repo.get(portfolio_id)
    if p is None or p.owner != user.username:
        # Not leaking existence-vs-ownership: both produce 404.
        raise NotFoundError(f"portfolio {portfolio_id} not found")
    return p


@router.get("/{portfolio_id}", response_model=Portfolio)
def get_portfolio(
    portfolio_id: Annotated[int, Path(ge=1)],
    portfolio_repo: PortfolioRepoDep,
    user: Annotated[User, Depends(get_current_user)],
) -> Portfolio:
    return _get_or_404(portfolio_repo, portfolio_id, user)


@router.delete(
    "/{portfolio_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_scope("portfolios:write"))],
)
def delete_portfolio(
    portfolio_id: Annotated[int, Path(ge=1)],
    portfolio_repo: PortfolioRepoDep,
    user: Annotated[User, Depends(get_current_user)],
) -> None:
    # First fetch with ownership check; only then delete.
    _get_or_404(portfolio_repo, portfolio_id, user)
    portfolio_repo.delete(portfolio_id)


@router.post(
    "/{portfolio_id}/holdings",
    response_model=Portfolio,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_scope("portfolios:write"))],
)
def add_holding(
    portfolio_id: Annotated[int, Path(ge=1)],
    payload: HoldingCreate,
    portfolio_repo: PortfolioRepoDep,
    asset_repo: AssetRepoDep,
    user: Annotated[User, Depends(get_current_user)],
) -> Portfolio:
    _get_or_404(portfolio_repo, portfolio_id, user)
    if asset_repo.get(payload.ticker) is None:
        raise ConflictError(f"unknown ticker: {payload.ticker!r}")
    updated = portfolio_repo.add_holding(
        portfolio_id, Holding(ticker=payload.ticker, quantity=payload.quantity)
    )
    assert updated is not None  # _get_or_404 already verified existence
    return updated


@router.delete(
    "/{portfolio_id}/holdings/{ticker}",
    response_model=Portfolio,
    dependencies=[Depends(require_scope("portfolios:write"))],
)
def remove_holding(
    portfolio_id: Annotated[int, Path(ge=1)],
    ticker: Annotated[str, Path(pattern=r"^[A-Za-z.]{1,10}$")],
    portfolio_repo: PortfolioRepoDep,
    user: Annotated[User, Depends(get_current_user)],
) -> Portfolio:
    existing = _get_or_404(portfolio_repo, portfolio_id, user)
    has_ticker = any(h.ticker == ticker.upper() for h in existing.holdings)
    if not has_ticker:
        raise NotFoundError(f"holding {ticker.upper()!r} not in portfolio {portfolio_id}")
    updated = portfolio_repo.remove_holding(portfolio_id, ticker)
    assert updated is not None
    return updated
