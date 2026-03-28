from pydantic import BaseModel, Field, model_validator

from app.schemas.common import (
    ATSEndpoint,
    LinkedInEndpoint,
    PaginationParams,
    SourceType,
)
from app.schemas.filters import ATSFilters, LinkedInFilters, SharedFilters


class JobSearchRequest(BaseModel):
    """Main request model for job search."""

    # ── Primary input ────────────────────────────────────────────────────
    # Either provide titles directly, or use client_id to pick up stored job_roles
    titles: list[str] | None = Field(
        None,
        description="Job titles/roles to search for. If not provided, uses job_roles from client config.",
        examples=[["Software Engineer", "Backend Developer"]],
    )

    # ── Source selection ──────────────────────────────────────────────────
    source: SourceType = Field(
        SourceType.BOTH,
        description="Which API to query: 'linkedin', 'ats', or 'both'",
    )

    # ── Explicit title filter override (optional) ────────────────────────
    # If not provided, auto-generated from `titles` by query_builder
    title_filter: str | None = Field(
        None,
        description="Override: Google-style title search. Auto-generated from titles if not set.",
    )
    advanced_title_filter: str | None = Field(
        None,
        description=(
            "Override: Advanced title filter with operators (& | ! <-> :*). "
            "Cannot be used with title_filter."
        ),
    )

    # ── Shared filters ───────────────────────────────────────────────────
    filters: SharedFilters = Field(
        default_factory=SharedFilters,
        description="Filters common to both ATS and LinkedIn APIs",
    )

    # ── Source-specific filters ───────────────────────────────────────────
    ats_filters: ATSFilters | None = Field(
        None,
        description="Additional filters specific to the ATS API",
    )
    linkedin_filters: LinkedInFilters | None = Field(
        None,
        description="Additional filters specific to the LinkedIn API",
    )

    # ── Endpoint selection ───────────────────────────────────────────────
    ats_endpoint: ATSEndpoint = Field(
        ATSEndpoint.ACTIVE_7D,
        description="Which ATS endpoint to hit",
    )
    linkedin_endpoint: LinkedInEndpoint = Field(
        LinkedInEndpoint.ACTIVE_7D,
        description="Which LinkedIn endpoint to hit",
    )

    # ── Pagination ───────────────────────────────────────────────────────
    pagination: PaginationParams = Field(
        default_factory=PaginationParams,
        description="Pagination settings (page, page_size)",
    )

    # ── Client context ───────────────────────────────────────────────────
    client_id: str | None = Field(
        None,
        description="Optional client ID to apply saved default filters",
    )

    @model_validator(mode="after")
    def validate_title_filters(self):
        if self.title_filter and self.advanced_title_filter:
            raise ValueError(
                "Cannot use both title_filter and advanced_title_filter. Choose one."
            )
        return self

    @model_validator(mode="after")
    def auto_switch_linkedin_endpoint_for_description(self):
        """Auto-switch to 24h endpoint if description_filter is used on LinkedIn 7d."""
        if (
            self.linkedin_filters
            and self.linkedin_filters.description_filter
            and self.linkedin_endpoint == LinkedInEndpoint.ACTIVE_7D
        ):
            self.linkedin_endpoint = LinkedInEndpoint.ACTIVE_24H
        return self
