"""Central orchestrator that coordinates job search across ATS and LinkedIn APIs."""

import asyncio
import json
import logging
import time

from app.core.config import Settings, get_settings
from app.schemas.common import SourceType
from app.schemas.request import JobSearchRequest
from app.schemas.response import SearchResponse
from app.services.fantastic_jobs.ats_client import ATSClient
from app.services.fantastic_jobs.linkedin_client import LinkedInClient
from app.services.fantastic_jobs.normalizer import (
    deduplicate_jobs,
    normalize_ats_response,
    normalize_linkedin_response,
)
from app.services.fantastic_jobs.query_builder import build_title_filter

logger = logging.getLogger("app.orchestrator")


class SearchOrchestrator:
    def __init__(self, settings: Settings | None = None):
        self._settings = settings or get_settings()
        self._ats_client = ATSClient(self._settings)
        self._linkedin_client = LinkedInClient(self._settings)

    async def execute(self, request: JobSearchRequest) -> SearchResponse:
        start_time = time.monotonic()

        # ── Log incoming request ─────────────────────────────────────────
        logger.info(
            "[REQUEST] ▶ Search started | titles=%s | source=%s | page=%d | page_size=%d",
            request.titles, request.source.value,
            request.pagination.page, request.pagination.page_size,
        )
        if request.client_id:
            logger.info("[CLIENT] Using client_id=%s (defaults will be merged)", request.client_id)

        # ── Step 1: Build title filter ───────────────────────────────────
        title_filter, advanced_title_filter = build_title_filter(
            titles=request.titles,
            title_filter_override=request.title_filter,
            advanced_title_filter_override=request.advanced_title_filter,
        )

        if title_filter:
            logger.info("[QUERY] title_filter = %s", title_filter)
        if advanced_title_filter:
            logger.info("[QUERY] advanced_title_filter = %s", advanced_title_filter)

        # ── Log filters being applied ────────────────────────────────────
        shared = request.filters
        active_filters = {
            k: v for k, v in shared.model_dump().items()
            if v is not None and v != [] and v != ""
        }
        if active_filters:
            logger.info("[QUERY] Shared filters: %s", json.dumps(active_filters, default=str))
        if request.ats_filters:
            ats_f = {k: v for k, v in request.ats_filters.model_dump().items() if v is not None}
            if ats_f:
                logger.info("[QUERY] ATS-specific filters: %s", json.dumps(ats_f, default=str))
        if request.linkedin_filters:
            li_f = {k: v for k, v in request.linkedin_filters.model_dump().items() if v is not None}
            if li_f:
                logger.info("[QUERY] LinkedIn-specific filters: %s", json.dumps(li_f, default=str))

        # ── Step 2: Determine sources ────────────────────────────────────
        query_ats = request.source in (SourceType.ATS, SourceType.BOTH)
        query_linkedin = request.source in (SourceType.LINKEDIN, SourceType.BOTH)
        is_both = request.source == SourceType.BOTH

        sources_queried = []
        if query_ats:
            sources_queried.append("ats")
        if query_linkedin:
            sources_queried.append("linkedin")

        if is_both:
            logger.info("[QUERY] Querying BOTH sources in parallel (exclude_ats_duplicate=true auto-set)")
        else:
            logger.info("[QUERY] Querying source: %s", sources_queried)

        # ── Step 3: Fan out API calls ────────────────────────────────────
        all_jobs = []
        errors = {}
        tasks = []

        if query_ats:
            tasks.append(("ats", self._search_ats(request, title_filter, advanced_title_filter)))
        if query_linkedin:
            tasks.append(("linkedin", self._search_linkedin(
                request, title_filter, advanced_title_filter, force_dedup=is_both,
            )))

        results = await asyncio.gather(
            *[t[1] for t in tasks],
            return_exceptions=True,
        )

        for (source_name, _), result in zip(tasks, results):
            if isinstance(result, Exception):
                logger.error("[ERROR] %s API failed: %s", source_name.upper(), result)
                errors[source_name] = str(result)
            else:
                logger.info(
                    "[NORMALIZER] %s → %d jobs normalized",
                    source_name.upper(), len(result),
                )
                all_jobs.extend(result)

        # ── Step 4: Deduplicate ──────────────────────────────────────────
        if is_both and len(all_jobs) > 0:
            before_count = len(all_jobs)
            all_jobs = deduplicate_jobs(all_jobs)
            removed = before_count - len(all_jobs)
            if removed > 0:
                logger.info("[NORMALIZER] Dedup removed %d duplicates (%d → %d)", removed, before_count, len(all_jobs))

        # ── Step 5: Build response ───────────────────────────────────────
        elapsed = time.monotonic() - start_time
        has_more = len(all_jobs) >= request.pagination.limit

        # Log summary
        logger.info(
            "[RESPONSE] ◀ Search complete | %d jobs | sources=%s | %.2fs%s",
            len(all_jobs), sources_queried, elapsed,
            f" | has_more={has_more}" if has_more else "",
        )
        if all_jobs:
            sample = all_jobs[:3]
            for i, j in enumerate(sample):
                logger.info(
                    "[RESPONSE]   %d. [%s] %s @ %s | %s | remote=%s",
                    i + 1, j.source_api.upper(), j.title, j.organization,
                    j.location or "N/A", j.is_remote,
                )
            if len(all_jobs) > 3:
                logger.info("[RESPONSE]   ... and %d more", len(all_jobs) - 3)

        if errors:
            logger.warning("[ERROR] Errors in response: %s", errors)

        return SearchResponse(
            jobs=all_jobs,
            total_results=len(all_jobs),
            page=request.pagination.page,
            page_size=request.pagination.page_size,
            has_more=has_more,
            sources_queried=sources_queried,
            metadata={
                "elapsed_seconds": round(elapsed, 3),
                "title_filter_used": title_filter,
                "advanced_title_filter_used": advanced_title_filter,
                "errors": errors if errors else None,
            },
        )

    async def _search_ats(
        self,
        request: JobSearchRequest,
        title_filter: str | None,
        advanced_title_filter: str | None,
    ) -> list:
        raw_data = await self._ats_client.search(
            endpoint=request.ats_endpoint.value,
            title_filter=title_filter,
            advanced_title_filter=advanced_title_filter,
            shared_filters=request.filters,
            ats_filters=request.ats_filters,
            limit=request.pagination.limit,
            offset=request.pagination.offset,
        )
        jobs_list = _extract_jobs_list(raw_data)
        return normalize_ats_response(jobs_list)

    async def _search_linkedin(
        self,
        request: JobSearchRequest,
        title_filter: str | None,
        advanced_title_filter: str | None,
        force_dedup: bool = False,
    ) -> list:
        raw_data = await self._linkedin_client.search(
            endpoint=request.linkedin_endpoint.value,
            title_filter=title_filter,
            advanced_title_filter=advanced_title_filter,
            shared_filters=request.filters,
            linkedin_filters=request.linkedin_filters,
            limit=request.pagination.limit,
            offset=request.pagination.offset,
            force_exclude_ats_duplicate=force_dedup,
        )
        jobs_list = _extract_jobs_list(raw_data)
        return normalize_linkedin_response(jobs_list)


def _extract_jobs_list(raw_data) -> list[dict]:
    """Extract the jobs list from API response."""
    if isinstance(raw_data, list):
        return raw_data
    if isinstance(raw_data, dict):
        for key in ("data", "jobs", "results", "items"):
            if key in raw_data and isinstance(raw_data[key], list):
                return raw_data[key]
        return [raw_data]
    return []
