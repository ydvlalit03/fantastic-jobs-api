from typing import Any, Literal

from pydantic import BaseModel, Field


class NormalizedJob(BaseModel):
    """Unified job record from either ATS or LinkedIn API."""

    # ── Core fields ──────────────────────────────────────────────────────
    id: str = Field(..., description="Unique job ID from source")
    title: str
    organization: str | None = None
    location: str | None = None
    url: str | None = Field(None, description="Application / job posting URL")
    source_api: Literal["ats", "linkedin"]
    source_platform: str | None = Field(
        None, description="ATS platform name (e.g., 'greenhouse', 'workday') or 'linkedin'"
    )
    date_posted: str | None = None
    date_indexed: str | None = None
    is_expired: bool | None = None

    # ── Location details ─────────────────────────────────────────────────
    city: str | None = None
    state: str | None = None
    country: str | None = None
    is_remote: bool | None = None

    # ── Description ──────────────────────────────────────────────────────
    description_text: str | None = None
    description_html: str | None = None

    # ── Salary ───────────────────────────────────────────────────────────
    salary_raw: str | None = None
    ai_salary_min: float | None = None
    ai_salary_max: float | None = None
    ai_salary_currency: str | None = None
    ai_salary_period: str | None = None

    # ── AI enrichment ────────────────────────────────────────────────────
    ai_employment_type: str | None = None
    ai_taxonomy: list[str] | None = None
    ai_work_arrangement: str | None = None
    ai_experience_level: str | None = None
    ai_visa_sponsorship: bool | None = None
    ai_skills: list[str] | None = None

    # ── LinkedIn company data ────────────────────────────────────────────
    li_company_slug: str | None = None
    li_company_name: str | None = None
    li_industry: str | None = None
    li_employee_count: int | None = None
    li_company_description: str | None = None
    li_headquarters: str | None = None
    li_followers: int | None = None

    # ── Raw passthrough ──────────────────────────────────────────────────
    raw: dict[str, Any] | None = Field(None, exclude=True)


class SearchResponse(BaseModel):
    """Response from a job search request."""

    jobs: list[NormalizedJob]
    total_results: int = Field(..., description="Total jobs returned in this response")
    page: int
    page_size: int
    has_more: bool = Field(
        ..., description="Whether more results are available via pagination"
    )
    sources_queried: list[str] = Field(
        ..., description="Which APIs were queried: ['ats'], ['linkedin'], or ['ats', 'linkedin']"
    )
    metadata: dict[str, Any] | None = Field(
        None, description="Extra info: timing, rate limit headers, etc."
    )
