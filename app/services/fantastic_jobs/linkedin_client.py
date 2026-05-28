"""HTTP client for the LinkedIn Job Search API on RapidAPI."""

import asyncio
import logging

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import Settings
from app.core.exceptions import RapidAPIError, RateLimitExceeded
from app.schemas.filters import LinkedInFilters, SharedFilters
from app.services.fantastic_jobs.query_builder import format_comma_list, format_taxonomy_list

logger = logging.getLogger("app.linkedin_client")


class LinkedInClient:
    def __init__(self, settings: Settings):
        self.base_url = settings.LINKEDIN_API_BASE_URL
        self.headers = {
            "X-RapidAPI-Key": settings.RAPIDAPI_KEY,
            "X-RapidAPI-Host": settings.LINKEDIN_API_HOST,
            "Content-Type": "application/json",
        }
        self.timeout = settings.HTTP_TIMEOUT
        self._semaphore = asyncio.Semaphore(settings.RAPIDAPI_MAX_CONCURRENT)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(httpx.HTTPStatusError),
    )
    async def search(
        self,
        endpoint: str,
        title_filter: str | None,
        advanced_title_filter: str | None,
        shared_filters: SharedFilters,
        linkedin_filters: LinkedInFilters | None,
        limit: int,
        offset: int,
        force_exclude_ats_duplicate: bool = False,
    ) -> dict:
        params = self._build_params(
            title_filter, advanced_title_filter,
            shared_filters, linkedin_filters, limit, offset,
            force_exclude_ats_duplicate,
        )

        import json as _json
        import time

        async with self._semaphore:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.base_url}{endpoint}"
                logger.info("[LINKEDIN-API] ▶ GET %s", url)
                logger.info("[LINKEDIN-API] QueryString: %s", _json.dumps(params, default=str))

                t0 = time.monotonic()
                resp = await client.get(url, params=params, headers=self.headers)
                elapsed = time.monotonic() - t0

                logger.info(
                    "[LINKEDIN-API] ◀ %d | %.2fs | content-length=%s",
                    resp.status_code, elapsed,
                    resp.headers.get("content-length", "?"),
                )

                if resp.status_code == 429:
                    retry_after = resp.headers.get("Retry-After")
                    logger.warning("[LINKEDIN-API] Rate limited! Retry-After=%s", retry_after)
                    raise RateLimitExceeded(
                        "LinkedIn",
                        int(retry_after) if retry_after else None,
                    )

                if resp.status_code >= 400:
                    logger.error("[LINKEDIN-API] Error response: %s", resp.text[:500])
                    raise RapidAPIError("LinkedIn", resp.status_code, resp.text[:500])

                data = resp.json()
                count = len(data) if isinstance(data, list) else "dict"
                logger.info("[LINKEDIN-API] Raw response: %s items", count)
                return data

    def _build_params(
        self,
        title_filter: str | None,
        advanced_title_filter: str | None,
        shared: SharedFilters,
        li: LinkedInFilters | None,
        limit: int,
        offset: int,
        force_exclude_ats_duplicate: bool,
    ) -> dict:
        params: dict = {
            "limit": str(limit),
            "offset": str(offset),
        }

        # Title
        if title_filter:
            params["title_filter"] = title_filter
        if advanced_title_filter:
            params["advanced_title_filter"] = advanced_title_filter

        # Shared filters
        if shared.location_filter:
            params["location_filter"] = shared.location_filter
        if shared.organization_filter:
            params["organization_filter"] = shared.organization_filter
        if shared.organization_exclusion_filter:
            params["organization_exclusion_filter"] = shared.organization_exclusion_filter
        if shared.advanced_organization_filter:
            params["advanced_organization_filter"] = shared.advanced_organization_filter
        if shared.description_type:
            params["description_type"] = shared.description_type.value
        if shared.remote is not None:
            params["remote"] = str(shared.remote).lower()
        if shared.agency is not None:
            params["agency"] = str(shared.agency).lower()
        if shared.date_filter:
            params["date_filter"] = shared.date_filter

        # AI flags
        if shared.include_ai:
            params["include_ai"] = "true"
        if shared.include_li:
            params["include_li"] = "true"

        # AI filters
        if shared.ai_employment_type_filter:
            params["ai_employment_type_filter"] = format_comma_list(
                [e.value for e in shared.ai_employment_type_filter]
            )
        if shared.ai_work_arrangement_filter:
            params["ai_work_arrangement_filter"] = format_comma_list(
                [w.value for w in shared.ai_work_arrangement_filter]
            )
        if shared.ai_has_salary is not None:
            params["ai_has_salary"] = str(shared.ai_has_salary).lower()
        if shared.ai_visa_sponsorship_filter is not None:
            params["ai_visa_sponsorship_filter"] = str(shared.ai_visa_sponsorship_filter).lower()
        if shared.ai_taxonomies_a_filter:
            params["ai_taxonomies_a_filter"] = format_taxonomy_list(shared.ai_taxonomies_a_filter)
        if shared.ai_taxonomies_a_primary_filter:
            params["ai_taxonomies_a_primary_filter"] = format_taxonomy_list(
                shared.ai_taxonomies_a_primary_filter
            )
        if shared.ai_taxonomies_a_exclusion_filter:
            params["ai_taxonomies_a_exclusion_filter"] = format_taxonomy_list(
                shared.ai_taxonomies_a_exclusion_filter
            )

        # LinkedIn company fields (on LinkedIn API these use li_ prefix too)
        if shared.li_organization_slug_filter:
            params["li_organization_slug_filter"] = shared.li_organization_slug_filter
        if shared.li_organization_slug_exclusion_filter:
            params["li_organization_slug_exclusion_filter"] = shared.li_organization_slug_exclusion_filter
        if shared.li_industry_filter:
            params["li_industry_filter"] = shared.li_industry_filter
        if shared.li_organization_specialties_filter:
            params["li_organization_specialties_filter"] = shared.li_organization_specialties_filter
        if shared.li_organization_description_filter:
            params["li_organization_description_filter"] = shared.li_organization_description_filter
        if shared.li_organization_employees_lte is not None:
            params["li_organization_employees_lte"] = str(shared.li_organization_employees_lte)
        if shared.li_organization_employees_gte is not None:
            params["li_organization_employees_gte"] = str(shared.li_organization_employees_gte)

        # LinkedIn-specific filters
        if li:
            if li.description_filter:
                params["description_filter"] = li.description_filter
            if li.organization_description_filter:
                params["organization_description_filter"] = li.organization_description_filter
            if li.organization_specialties_filter:
                params["organization_specialties_filter"] = li.organization_specialties_filter
            if li.organization_slug_filter:
                params["organization_slug_filter"] = li.organization_slug_filter
            if li.type_filter:
                params["type_filter"] = format_comma_list(
                    [t.value for t in li.type_filter]
                )
            if li.seniority_filter:
                params["seniority_filter"] = format_comma_list(
                    [s.value for s in li.seniority_filter]
                )
            if li.external_apply_url is not None:
                params["external_apply_url"] = str(li.external_apply_url).lower()
            if li.directApply is not None:
                params["directApply"] = str(li.directApply).lower()
            if li.employees_lte is not None:
                params["employees_lte"] = str(li.employees_lte)
            if li.employees_gte is not None:
                params["employees_gte"] = str(li.employees_gte)
            if li.order:
                params["order"] = li.order.value
            if li.ai_experience_level_filter:
                params["ai_experience_level_filter"] = format_comma_list(
                    [e.value for e in li.ai_experience_level_filter]
                )

            # exclude_ats_duplicate: use explicit value or force flag
            if li.exclude_ats_duplicate is not None:
                params["exclude_ats_duplicate"] = str(li.exclude_ats_duplicate).lower()
            elif force_exclude_ats_duplicate:
                params["exclude_ats_duplicate"] = "true"

        elif force_exclude_ats_duplicate:
            params["exclude_ats_duplicate"] = "true"

        return params
