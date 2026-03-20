import math
from typing import Any, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class InfluencerMatcherInput(BaseModel):
    requirements: str = Field(..., description="The product's requirements for the influencer match.")


class InfuencerMatcherRequestInput(BaseModel):
    campaign_id: UUID
    s3_pdf_links: str | List[str]
    description: Optional[str] = None
    brand_template: Optional[dict] = None
    brand_id: Optional[str] = None


class RecommendInfluencer(BaseModel):
    id: str = Field(..., description="The unique identifier of the influencer.")
    unique_id: str = Field(..., description="The unique username or handle of the influencer.")
    nickname: str = Field(..., description="The nickname of the influencer.")
    signature: Optional[Any] = Field(None, description="The signature or bio of the influencer.")
    total_followers: Optional[Union[int, float]] = Field(
        None, description="The total number of followers the influencer has."
    )
    main_category: Optional[List[str]] = Field(
        None, description="The main categories the influencer is associated with."
    )

    @model_validator(mode="before")
    @classmethod
    def convert_nan_values(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Handle signature field
            if "signature" in data and isinstance(data["signature"], float) and math.isnan(data["signature"]):
                data["signature"] = None

            # Handle total_followers field
            if (
                "total_followers" in data
                and isinstance(data["total_followers"], float)
                and math.isnan(data["total_followers"])
            ):
                data["total_followers"] = None

            # Handle main_category field
            if (
                "main_category" in data
                and isinstance(data["main_category"], float)
                and math.isnan(data["main_category"])
            ):
                data["main_category"] = None
        return data

    @field_validator("signature")
    @classmethod
    def validate_signature(cls, v: Any) -> Any:
        if v is None:
            return v
        return str(v)


class InfluencerMatcherResponse(BaseModel):
    input_metadata: dict = Field(..., description="The extracted input metadata from the user query.")
    recommend_plan: Optional[str] = Field(None, description="The recommended plan for the influencer match.")
    rec_table_division: Optional[dict] = Field(
        None, description="The recommended table division for the influencer match."
    )
    rec_plan_summary: str = Field(..., description="The summary of the recommended plan.")
    recommend_influencers: Optional[List[RecommendInfluencer]] = Field(
        None, description="The recommended influencers for the campaign."
    )
    debug_info: Optional[dict] = Field(None, description="Debug information about the state of the graph.")
    campaign_id: str = Field(..., description="The unique identifier of the campaign.")


class InputMetadata(BaseModel):
    """User query with description"""

    model_config = ConfigDict(extra="allow")
    initial_budget_plan: int = 0
    number_of_video_or_koc: int = 0
