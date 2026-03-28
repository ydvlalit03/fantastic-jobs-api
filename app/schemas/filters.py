from pydantic import BaseModel, Field

from app.schemas.common import (
    DescriptionType,
    EmploymentType,
    ExperienceLevelATS,
    ExperienceLevelLinkedIn,
    LinkedInJobType,
    SeniorityLevel,
    SortOrder,
    WorkArrangement,
)


class SharedFilters(BaseModel):
    """Filters common to both ATS and LinkedIn APIs."""

    # Location
    location_filter: str | None = Field(
        None,
        description=(
            "Filter on location. Use full names (e.g., 'United States', 'New York'). "
            "Use OR for multiple: 'Dubai OR Netherlands OR Belgium'"
        ),
    )

    # Organization
    organization_filter: str | None = Field(
        None,
        description="Filter by exact company name. Comma-delimited, no spaces. E.g., 'NVIDIA,Walmart'",
    )
    organization_exclusion_filter: str | None = Field(
        None,
        description="Exclude companies by exact name. Comma-delimited, no spaces.",
    )
    advanced_organization_filter: str | None = Field(
        None,
        description=(
            "Advanced org filter with operators: & (AND), | (OR), ! (NOT), "
            "<-> (FOLLOWED BY), :* (Prefix Wildcard). "
            "E.g., \"University & ! Harvard\""
        ),
    )

    # Description
    description_type: DescriptionType = Field(
        DescriptionType.TEXT,
        description="Response description format. 'text', 'html', or '' (no description)",
    )

    # Remote / Agency
    remote: bool | None = Field(
        None,
        description="true=remote only, false=non-remote only, null=both",
    )
    agency: bool | None = Field(
        None,
        description="true=recruitment agencies only, false=regular companies only, null=both",
    )

    # Date
    date_filter: str | None = Field(
        None,
        description=(
            "Greater-than date filter. Format: '2025-01-01' or '2025-01-01T14:00:00'. "
            "UTC timezone. 1-2 hour delay before jobs appear."
        ),
    )

    # AI enrichment flags
    include_ai: bool = Field(
        True,
        description="Include AI-enriched fields (employment type, taxonomy, salary, etc.)",
    )
    include_li: bool = Field(
        True,
        description="Include LinkedIn company profile data (~93% coverage)",
    )

    # AI filters
    ai_employment_type_filter: list[EmploymentType] | None = Field(
        None,
        description="Filter by AI-identified employment type. E.g., [FULL_TIME, PART_TIME]",
    )
    ai_work_arrangement_filter: list[WorkArrangement] | None = Field(
        None,
        description="Filter by work arrangement: On-site, Hybrid, Remote OK, Remote Solely",
    )
    ai_has_salary: bool | None = Field(
        None,
        description="true=only jobs with salary (raw or AI-extracted). Requires include_ai=true.",
    )
    ai_visa_sponsorship_filter: bool | None = Field(
        None,
        description="true=only jobs mentioning visa sponsorship",
    )
    ai_taxonomies_a_filter: list[str] | None = Field(
        None,
        description=(
            "Filter by top-level taxonomy. E.g., ['Technology', 'Healthcare']. "
            "For taxonomies with &, they will be double-quoted automatically."
        ),
    )
    ai_taxonomies_a_primary_filter: list[str] | None = Field(
        None,
        description="Filter by primary taxonomy only (first in array)",
    )
    ai_taxonomies_a_exclusion_filter: list[str] | None = Field(
        None,
        description="Exclude jobs with certain taxonomies",
    )

    # LinkedIn company fields (available on both APIs)
    li_organization_slug_filter: str | None = Field(
        None,
        description="Filter by LinkedIn company slug. Comma-delimited, no spaces. E.g., 'netflix,walmart'",
    )
    li_organization_slug_exclusion_filter: str | None = Field(
        None,
        description="Exclude companies by LinkedIn slug. Comma-delimited, no spaces.",
    )
    li_industry_filter: str | None = Field(
        None,
        description="Filter by LinkedIn industry. Exact, case-sensitive. Comma-delimited, no spaces.",
    )
    li_organization_specialties_filter: str | None = Field(
        None,
        description="Filter by LinkedIn company specialties. Google-style search.",
    )
    li_organization_description_filter: str | None = Field(
        None,
        description="Filter by LinkedIn company description. Google-style search.",
    )
    li_organization_employees_lte: int | None = Field(
        None, ge=0,
        description="Max company size (employees). Use with employees_gte to set range.",
    )
    li_organization_employees_gte: int | None = Field(
        None, ge=0,
        description="Min company size (employees). Use with employees_lte to set range.",
    )


class ATSFilters(BaseModel):
    """Filters specific to the Active Jobs DB (ATS/Career Site) API."""

    description_filter: str | None = Field(
        None,
        description="Filter on job description. Google-style search.",
    )
    advanced_description_filter: str | None = Field(
        None,
        description=(
            "Advanced description filter with operators: & (AND), | (OR), ! (NOT), "
            "<-> (FOLLOWED BY), :* (Prefix Wildcard)."
        ),
    )
    source: list[str] | None = Field(
        None,
        description=(
            "Filter by ATS platform. E.g., ['workday', 'greenhouse']. "
            "Options: adp, applicantpro, ashby, bamboohr, greenhouse, lever.co, workday, etc."
        ),
    )
    source_exclusion: list[str] | None = Field(
        None,
        description="Exclude ATS platforms. E.g., ['workday', 'greenhouse']",
    )
    ai_experience_level_filter: list[ExperienceLevelATS] | None = Field(
        None,
        description="Filter by experience level (ATS scale): 0-2, 2-5, 5-10, 10+",
    )


class LinkedInFilters(BaseModel):
    """Filters specific to the LinkedIn Job Search API."""

    description_filter: str | None = Field(
        None,
        description=(
            "Filter on job description. WARNING: risky on 7-day endpoint (timeouts). "
            "Best used with 24h or Hourly endpoints."
        ),
    )
    organization_description_filter: str | None = Field(
        None,
        description="Filter on org's LinkedIn description + specialties. Google-style.",
    )
    organization_specialties_filter: str | None = Field(
        None,
        description="Filter on org's LinkedIn specialties. Google-style.",
    )
    organization_slug_filter: str | None = Field(
        None,
        description="Filter by company slug. Comma-delimited, no spaces. Exact match only.",
    )
    type_filter: list[LinkedInJobType] | None = Field(
        None,
        description="Filter by job type: CONTRACTOR, FULL_TIME, INTERN, OTHER, PART_TIME, TEMPORARY, VOLUNTEER",
    )
    seniority_filter: list[SeniorityLevel] | None = Field(
        None,
        description=(
            "Filter by seniority. Case-sensitive. Options: Associate, Director, Executive, "
            "Mid-Senior level, Entry level, Not Applicable, Internship"
        ),
    )
    exclude_ats_duplicate: bool | None = Field(
        None,
        description="Remove duplicates with Active Jobs DB. Auto-set to true when source='both'.",
    )
    external_apply_url: bool | None = Field(
        None,
        description="true=only jobs with external apply URL",
    )
    directApply: bool | None = Field(
        None,
        description="Include/exclude LinkedIn EasyApply jobs",
    )
    employees_lte: int | None = Field(
        None, ge=0,
        description="Max company employees (LinkedIn native field)",
    )
    employees_gte: int | None = Field(
        None, ge=0,
        description="Min company employees (LinkedIn native field)",
    )
    order: SortOrder | None = Field(
        None,
        description="Sort order by date. Default: desc (newest first)",
    )
    ai_experience_level_filter: list[ExperienceLevelLinkedIn] | None = Field(
        None,
        description="Filter by experience level (LinkedIn scale): 0-3, 2-5, 5-10, 10+",
    )
