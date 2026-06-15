"""Asset domain models — same shape used since notebook 1.3."""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AssetClass(str, Enum):
    EQUITY = "equity"
    BOND = "bond"
    CASH = "cash"


class AssetCreate(BaseModel):
    """Inbound payload for creating an asset."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {"ticker": "AAPL", "name": "Apple Inc.", "price": 190.0, "asset_class": "equity"}
        },
    )

    ticker: str = Field(pattern=r"^[A-Z.]{1,10}$", description="1-10 uppercase letters / dots")
    name: str = Field(min_length=1, max_length=120)
    price: float = Field(ge=0)
    asset_class: AssetClass = AssetClass.EQUITY

    @field_validator("ticker", mode="before")
    @classmethod
    def _upper(cls, v):
        return v.upper() if isinstance(v, str) else v


class Asset(AssetCreate):
    """Outbound representation. Identical fields; separated so the response model
    can diverge later (e.g., add a `last_updated` field) without changing inbound."""

    model_config = ConfigDict(extra="forbid")
