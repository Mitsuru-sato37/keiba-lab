from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class RecommendationPolicy(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    min_ev: Decimal = Field(gt=0)
    max_uncertainty: Decimal = Field(ge=0, le=1)
    policy_version: str = Field(min_length=1)

    def __init__(self, **data: object) -> None:
        data.setdefault("min_ev", Decimal("1.05"))
        data.setdefault("max_uncertainty", Decimal("0.30"))
        data.setdefault("policy_version", "POLICY-WIN-001:v1")
        super().__init__(**data)
