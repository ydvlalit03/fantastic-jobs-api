from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import SourceType
from app.schemas.filters import ATSFilters, LinkedInFilters, SharedFilters


class ClientConfigCreate(BaseModel):
    """Schema for onboarding a new client."""

    client_id: str = Field(..., description="Unique client identifier")
    client_name: str = Field(..., description="Human-readable client name")

    # Job roles from the Job Roles API (set once during onboarding)
    job_roles: list[str] = Field(
        ...,
        min_length=1,
        description="Job roles/titles from the Job Roles API. Set once during onboarding.",
        examples=[["Software Engineer", "Backend Developer", "Data Engineer"]],
    )

    default_source: SourceType = Field(
        SourceType.BOTH,
        description="Default API source preference",
    )
    default_shared_filters: SharedFilters = Field(
        default_factory=SharedFilters,
        description="Default shared filters applied to every search",
    )
    default_ats_filters: ATSFilters | None = Field(
        None, description="Default ATS-specific filters"
    )
    default_linkedin_filters: LinkedInFilters | None = Field(
        None, description="Default LinkedIn-specific filters"
    )


class ClientConfigUpdate(BaseModel):
    """Schema for updating client configuration. All fields optional."""

    client_name: str | None = None
    job_roles: list[str] | None = None
    default_source: SourceType | None = None
    default_shared_filters: SharedFilters | None = None
    default_ats_filters: ATSFilters | None = None
    default_linkedin_filters: LinkedInFilters | None = None


class ClientConfigRead(BaseModel):
    """Schema for reading client configuration."""

    id: int
    client_id: str
    client_name: str
    job_roles: list[str] | None
    default_source: str
    default_shared_filters: dict
    default_ats_filters: dict | None
    default_linkedin_filters: dict | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
