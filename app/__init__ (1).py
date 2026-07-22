from typing import Literal, Optional

from pydantic import BaseModel, Field

FloorsOption = Literal["Ground only", "G + 1", "G + 2"]


class ComplianceCheckRequest(BaseModel):
    frontage_ft: float = Field(..., gt=0, description="Road-facing plot width, in feet")
    depth_ft: float = Field(..., gt=0, description="Front-to-back plot depth, in feet")
    road_ft: float = Field(..., gt=0, description="Abutting road width, in feet")
    floors: FloorsOption = "G + 1"


class ComplianceCheckResponse(BaseModel):
    id: int
    created_at: str
    frontage_ft: float
    depth_ft: float
    road_ft: float
    floors: str
    front_ft: float
    side_ft: float
    rear_ft: float
    side_applies_to: str
    plot_sqft: float
    max_fsi_sqft: float
    buildable_sqft: float
    parking: int
    warning: Optional[str]
    rules_version: str
