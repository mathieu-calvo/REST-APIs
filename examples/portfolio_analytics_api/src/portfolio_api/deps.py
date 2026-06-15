"""Shared DI providers — repos are stashed on app.state by the lifespan."""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from portfolio_api.repositories.assets import AssetRepo
from portfolio_api.repositories.portfolios import PortfolioRepo


def get_asset_repo(request: Request) -> AssetRepo:
    """The active AssetRepo, opened on startup by the lifespan."""
    return request.app.state.asset_repo


def get_portfolio_repo(request: Request) -> PortfolioRepo:
    return request.app.state.portfolio_repo


AssetRepoDep = Annotated[AssetRepo, Depends(get_asset_repo)]
PortfolioRepoDep = Annotated[PortfolioRepo, Depends(get_portfolio_repo)]
