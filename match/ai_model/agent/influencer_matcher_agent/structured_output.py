from typing import List, Literal, Optional

from pydantic import BaseModel, Field, PrivateAttr, computed_field, model_validator
from typing_extensions import Self

from match.ai_model.agent.influencer_matcher_agent.constants import ALLOWED_INDUSTRIES
from match.ai_model.agent.influencer_matcher_agent.utils import get_price


class RelevantIndustries(BaseModel):
    """Relevant industries of Kocs with product descriptions"""

    industries: List[Literal[ALLOWED_INDUSTRIES]] = Field(
        ...,
        description="List of all relevant industries of Kocs with product descriptions",
    )


class Segment(BaseModel):
    lower_bound: int = Field(
        description="Lower bound of the segment in the full precision. For example, 1k = 1000, 10k = 10000, 100k = 1000000, etc."  # noqa: E501
    )  # noqa: E501
    upper_bound: int = Field(
        description="Upper bound of the segment in the full precision. For example, 1k = 1000, 10k = 10000, 100k = 1000000, `etc."  # noqa: E501
    )  # noqa: E501


class SegmentPlan(BaseModel):
    segment: Segment = Field(description="Upper and lower bounds of the segment in full precision.")
    number: int = Field(description="Number of needed video in the segment")
    note: str = Field(description="Note for the segment")
    emoji: str = Field(description="Emoji for the segment")

    _percentage = PrivateAttr(default_factory=float)
    _est_avg_price = PrivateAttr(default_factory=float)
    _est_total_price = PrivateAttr(default_factory=float)

    def set_percentage(self, value: float) -> None:
        """Set the percentage value."""
        self._percentage = value

    def set_est_avg_price(self, value: float) -> None:
        """Set the estimated average price value."""
        self._est_avg_price = value

    def set_est_total_price(self, value: float) -> None:
        """Set the estimated total price value."""
        self._est_total_price = value

    @computed_field  # type: ignore
    @property
    def percentage(self) -> float:
        """Percentage of the segment in the plan"""
        return self._percentage

    @computed_field  # type: ignore
    @property
    def est_avg_price(self) -> float:
        """Estimated average price of the segment"""
        return self._est_avg_price

    @computed_field  # type: ignore
    @property
    def est_total_price(self) -> float:
        """Estimated total price of the segment"""
        return self._est_total_price


class TableDevisionPlan(BaseModel):
    table_available: bool = Field(..., description="Is the devision table available?")
    plans: List[SegmentPlan] = Field(..., description="List of segments and their number of kocs")

    _total_number_of_koc_rec: float = PrivateAttr(0.0)
    _budget_rec: float = PrivateAttr(0.0)

    @model_validator(mode="after")
    def compute_percentage_and_price(self) -> Self:
        total_kocs = sum(p.number for p in self.plans)
        budget = 0.0

        for plan in self.plans:
            # compute and stash on the plan
            pct = (plan.number / total_kocs * 100) if total_kocs else 0
            plan.set_percentage(pct)
            plan.set_est_avg_price(get_price(plan.segment.upper_bound - 1))
            plan.set_est_total_price(plan.number * plan.est_avg_price)
            budget += plan.est_total_price

        # stash totals on self
        self._total_number_of_koc_rec = total_kocs
        self._budget_rec = budget
        return self

    @computed_field  # type: ignore
    @property
    def total_number_of_koc_rec(self) -> float:
        """Total number of kocs recommended"""
        return self._total_number_of_koc_rec

    @computed_field  # type: ignore
    @property
    def budget_rec(self) -> float:
        """Budget recommended"""
        return self._budget_rec


class ProductInfo(BaseModel):
    """Product description with relevant industries"""

    product_name: Optional[str] = Field(None, description="Product name")
    product_description: Optional[str] = Field(
        None,
        description="Product description",
    )


class UserQueryExtraction(BaseModel):
    """User query with description"""

    initial_budget_plan: Optional[int] = Field(None, description="Initial budget plan")
    number_of_video_or_koc: Optional[int] = Field(None, description="Number of planned video or koc")
    product_metadata: Optional[List[ProductInfo]] = Field(None, description="List of product information")
    additional_instructions: Optional[str] = Field(
        None,
        description="Any additional instructions, directives, or special notes mentioned in the requirements",
    )


class RecommendedCreatorsExtraction(BaseModel):
    """Recommended creators"""

    creator_ids: List[str] = Field(
        description="List of recommended creator IDs",
    )
