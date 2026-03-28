"""Single job search endpoint — POST /api/v1/job-search."""

import logging
import time

from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.schemas.job_search import JobSearchBody, JobType
from app.schemas.response import NormalizedJob, SearchResponse
from app.services.fantastic_jobs.ats_client import ATSClient
from app.services.fantastic_jobs.linkedin_client import LinkedInClient
from app.services.fantastic_jobs.normalizer import normalize_ats_response, normalize_linkedin_response
from app.services.fantastic_jobs.query_builder import build_title_filter

logger = logging.getLogger("app.job_search")

router = APIRouter(tags=["job-search"])


def _build_title_string(titles: list[str]) -> tuple[str | None, str | None]:
    """Convert list of titles to title_filter or advanced_title_filter."""
    return build_title_filter(titles)


def _build_location_string(locations: list[str] | None) -> str | None:
    """Convert list of locations to OR-separated string for the API."""
    if not locations:
        return None
    return " OR ".join(f'"{loc}"' for loc in locations)


def _extract_jobs_list(raw_data) -> list[dict]:
    """Extract the jobs list from various API response formats."""
    if isinstance(raw_data, list):
        return raw_data
    if isinstance(raw_data, dict):
        for key in ("data", "jobs", "results", "items"):
            if key in raw_data and isinstance(raw_data[key], list):
                return raw_data[key]
        return [raw_data]
    return []


@router.post(
    "/job-search",
    response_model=SearchResponse,
    summary="Search jobs from LinkedIn or ATS Career Sites",
    description="Single endpoint — pass type, titles, and optional filters. Returns normalized job listings.",
)
async def job_search(
    body: JobSearchBody,
    settings: Settings = Depends(get_settings),
):
    start_time = time.monotonic()

    logger.info(
        "[REQUEST] ▶ job-search | type=%s | titles=%s | limit=%d",
        body.type.value, body.advanced_title_filter, body.limit,
    )

    # ── Build title filter string from list ──────────────────────────────
    title_filter, advanced_title_filter = _build_title_string(body.advanced_title_filter)

    if title_filter:
        logger.info("[QUERY] title_filter = %s", title_filter)
    if advanced_title_filter:
        logger.info("[QUERY] advanced_title_filter = %s", advanced_title_filter)

    # ── Build location string from list ──────────────────────────────────
    location_string = _build_location_string(body.location_filter)
    if location_string:
        logger.info("[QUERY] location_filter = %s", location_string)

    # ── Build query params ───────────────────────────────────────────────
    params: dict = {"limit": str(body.limit), "offset": "0"}

    if title_filter:
        params["title_filter"] = title_filter
    if advanced_title_filter:
        params["advanced_title_filter"] = advanced_title_filter
    if location_string:
        params["location_filter"] = location_string
    if body.type_filter is not None:
        params["type_filter"] = body.type_filter.value
    if body.remote is not None:
        params["remote"] = str(body.remote).lower()
    if body.agency is not None:
        params["agency"] = str(body.agency).lower()
    if body.industry_filter:
        params["li_industry_filter"] = body.industry_filter
    if body.date_filter:
        params["date_filter"] = body.date_filter
    if body.exclude_ats_duplicate is not None:
        params["exclude_ats_duplicate"] = str(body.exclude_ats_duplicate).lower()
    if body.include_ai:
        params["include_ai"] = "true"

    # ── Call the correct upstream API ────────────────────────────────────
    all_jobs: list[NormalizedJob] = []
    source_name: str

    if body.type == JobType.LINKEDIN:
        source_name = "linkedin"
        client = LinkedInClient(settings)
        endpoint = "/active-jb-7d"

        # Auto-switch to 24h if description search would timeout on 7d
        raw_data = await _call_api(client, endpoint, params)
        jobs_list = _extract_jobs_list(raw_data)
        all_jobs = normalize_linkedin_response(jobs_list)

    else:  # ATS_CAREER_SITES
        source_name = "ats"
        client = ATSClient(settings)
        endpoint = "/active-ats-7d"

        raw_data = await _call_api(client, endpoint, params)
        jobs_list = _extract_jobs_list(raw_data)
        all_jobs = normalize_ats_response(jobs_list)

    # ── Build response ───────────────────────────────────────────────────
    elapsed = time.monotonic() - start_time

    logger.info(
        "[RESPONSE] ◀ %d jobs | source=%s | %.2fs",
        len(all_jobs), source_name, elapsed,
    )

    if all_jobs:
        for i, j in enumerate(all_jobs[:3]):
            logger.info(
                "[RESPONSE]   %d. [%s] %s @ %s | %s",
                i + 1, j.source_api.upper(), j.title, j.organization, j.location or "N/A",
            )
        if len(all_jobs) > 3:
            logger.info("[RESPONSE]   ... and %d more", len(all_jobs) - 3)

    return SearchResponse(
        jobs=all_jobs,
        total_results=len(all_jobs),
        page=1,
        page_size=body.limit,
        has_more=len(all_jobs) >= body.limit,
        sources_queried=[source_name],
        metadata={
            "elapsed_seconds": round(elapsed, 3),
            "title_filter_used": title_filter,
            "advanced_title_filter_used": advanced_title_filter,
            "errors": None,
        },
    )


async def _call_api(client, endpoint: str, params: dict) -> dict | list:
    """Call the upstream API using the raw params dict directly."""
    import httpx

    url = f"{client.base_url}{endpoint}"
    logger.info("[API] ▶ GET %s", url)
    logger.info("[API] Params: %s", params)

    async with client._semaphore:
        async with httpx.AsyncClient(timeout=client.timeout) as http:
            t0 = time.monotonic()
            resp = await http.get(url, params=params, headers=client.headers)
            elapsed = time.monotonic() - t0

            logger.info("[API] ◀ %d | %.2fs", resp.status_code, elapsed)

            if resp.status_code == 429:
                from app.core.exceptions import RateLimitExceeded
                raise RateLimitExceeded(
                    "API", int(resp.headers.get("Retry-After", 0)) or None
                )
            if resp.status_code >= 400:
                from app.core.exceptions import RapidAPIError
                raise RapidAPIError("API", resp.status_code, resp.text[:500])

            return resp.json()
