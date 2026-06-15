"""Portfolio + Holding models."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class HoldingCreate(BaseModel):
    """Inbound: add a holding to a portfolio."""

    model_config = ConfigDict(extra="forbid")

    ticker: str = Field(pattern=r"^[A-Z.]{1,10}$")
    quantity: float = Field(gt=0, description="Units held; fractional shares allowed")

    @field_validator("ticker", mode="before")
    @classmethod
    def _upper(cls, v):
        return v.upper() if isinstance(v, str) else v


class Holding(HoldingCreate):
    """Outbound holding."""

    model_config = ConfigDict(extra="forbid")


class PortfolioCreate(BaseModel):
    """Inbound: create an empty (or seeded) portfolio."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=80)
    holdings: list[HoldingCreate] = Field(default_factory=list)


class Portfolio(BaseModel):
    """Outbound portfolio."""

    model_config = ConfigDict(extra="forbid")

    id: int
    owner: str = Field(description="Username of the JWT subject that created this portfolio")
    name: str
    holdings: list[Holding] = Field(default_factory=list)
