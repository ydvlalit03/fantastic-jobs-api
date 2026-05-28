"""Flat request schema for POST /api/v1/job-search — matches upstream RapidAPI contract."""

from enum import Enum

from pydantic import BaseModel, Field


class JobType(str, Enum):
    LINKEDIN = "LINKEDIN"
    ATS_CAREER_SITES = "ATS_CAREER_SITES"


class TypeFilter(str, Enum):
    CONTRACTOR = "CONTRACTOR"
    FULL_TIME = "FULL_TIME"
    INTERN = "INTERN"
    OTHER = "OTHER"
    PART_TIME = "PART_TIME"
    TEMPORARY = "TEMPORARY"
    VOLUNTEER = "VOLUNTEER"


class JobSearchBody(BaseModel):
    """Flat request body — one endpoint, one contract."""

    type: JobType = Field(
        ...,
        description="LINKEDIN or ATS_CAREER_SITES (mandatory)",
    )
    advanced_title_filter: list[str] = Field(
        ...,
        min_length=1,
        description="Job titles to search (mandatory)",
        examples=[["Program Manager", "Salesforce Consultant", "Business Architect"]],
    )
    limit: int = Field(10, ge=1, le=100, description="Max results (default 10)")
    location_filter: list[str] | None = Field(
        None,
        description="Locations to filter by",
        examples=[["Atlanta", "Seattle", "Dallas"]],
    )
    type_filter: TypeFilter | None = Field(
        None,
        description="Employment type: CONTRACTOR, FULL_TIME, INTERN, OTHER, PART_TIME, TEMPORARY, VOLUNTEER",
    )
    remote: bool | None = Field(None, description="Filter for remote jobs")
    agency: bool | None = Field(None, description="Filter for agency jobs")
    industry_filter: str | None = Field(None, description="Industry filter (LinkedIn)")
    date_filter: str | None = Field(None, description="Date filter YYYY-MM-DD (UTC)")
    exclude_ats_duplicate: bool | None = Field(
        None,
        description="Exclude ATS duplicates (LinkedIn only)",
    )
    include_ai: bool = Field(True, description="Include AI enrichment data (default true)")
