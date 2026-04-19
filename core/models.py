"""
Pydantic models for Phase 1 schema validation.

PredictionRow validates entries from the inventory agent's predictions[] array
before they are written to prediction_log (D-01, D-02, D-03, D-04).

BaselineMetrics validates baseline_metrics JSONB before recommendation_outcomes
insert, enforcing the required-key set per action_type (D-05).
"""

from datetime import date
from typing import Literal

from pydantic import BaseModel, field_validator, model_validator


class PredictionRow(BaseModel):
    """Validates one entry from Claude's predictions[] array.

    Field names map 1:1 to prediction_log columns. Use .model_dump()
    to feed directly into supabase.table('prediction_log').insert().
    """

    product_id: str
    agent: str
    predicted_value: float       # days_of_supply at prediction time (e.g. 11.2)
    confidence: float
    snapshot_date: str           # "YYYY-MM-DD"
    resolution_date: str         # "YYYY-MM-DD" — snapshot_date + ceil(days_of_supply)
    resolution_status: Literal["pending", "accurate", "inaccurate"] = "pending"
    actual_outcome: float | None = None
    run_id: str | None = None
    reasoning: str = ""

    @field_validator("predicted_value")
    @classmethod
    def predicted_value_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError(
                f"predicted_value must be > 0 (got {v}). "
                "A value of 0 means already out of stock — write a critical alert, "
                "not a prediction row."
            )
        return round(v, 2)

    @field_validator("snapshot_date", "resolution_date")
    @classmethod
    def must_be_valid_iso_date(cls, v: str) -> str:
        # Raises ValueError on malformed date — caught by caller's try/except
        date.fromisoformat(v)
        return v

    @field_validator("confidence")
    @classmethod
    def confidence_in_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"confidence must be 0.0-1.0, got {v}")
        return round(v, 3)


# Required baseline keys per action_type — enforces D-05 from CONTEXT.md.
# Module-level constant matches core/config.py UPPER_SNAKE convention.
_REQUIRED_BASELINE_KEYS: dict[str, set[str]] = {
    "fba_replenishment": {
        "current_stock",
        "daily_velocity_7d",
        "daily_velocity_30d",
        "days_of_supply",
    },
    "price_change": {
        "current_price",
        "current_bsr",
        "revenue_7d",
    },
    "ppc_bid_change": {
        "current_bid",
        "acos_7d",
        "acos_30d",
        "spend_7d",
    },
    "ppc_budget_change": {
        "current_budget",
        "acos_7d",
        "acos_30d",
        "spend_30d",
    },
}


# Measurement window defaults per action_type — enforces D-06.
# Imported by executor/executor.py in Plan 03.
MEASUREMENT_WINDOWS: dict[str, int] = {
    "fba_replenishment": 30,
    "price_change":      14,
    "ppc_bid_change":     7,
    "ppc_budget_change": 14,
}


class BaselineMetrics(BaseModel):
    """Validates baseline_metrics JSONB before recommendation_outcomes insert.

    Ensures all required keys for the action_type (D-05) are present. Does NOT
    enforce key VALUES (NULLs allowed for unknown metrics), only key PRESENCE.
    """

    action_type: str
    metrics: dict

    @model_validator(mode="after")
    def required_keys_present(self) -> "BaselineMetrics":
        required = _REQUIRED_BASELINE_KEYS.get(self.action_type, set())
        missing = required - set(self.metrics.keys())
        if missing:
            raise ValueError(
                f"baseline_metrics for action_type='{self.action_type}' "
                f"is missing required keys: {sorted(missing)}. "
                f"Present keys: {sorted(set(self.metrics.keys()))}"
            )
        return self
