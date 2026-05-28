"""Job search endpoint — the main entry point for the wrapper API."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.models import ClientConfig
from app.db.session import get_db
from app.schemas.common import SourceType
from app.schemas.filters import ATSFilters, LinkedInFilters, SharedFilters
from app.schemas.request import JobSearchRequest
from app.schemas.response import SearchResponse
from app.services.fantastic_jobs.search_orchestrator import SearchOrchestrator

logger = logging.getLogger("app.search")

router = APIRouter(tags=["search"])


def get_orchestrator(settings: Settings = Depends(get_settings)) -> SearchOrchestrator:
    return SearchOrchestrator(settings)


@router.post(
    "/search",
    response_model=SearchResponse,
    summary="Search jobs across ATS and/or LinkedIn APIs",
    description=(
        "Provide titles directly, or pass client_id to use stored job_roles from onboarding. "
        "If client_id is provided, saved default filters and job_roles are merged. "
        "Request-level values always override client defaults."
    ),
)
async def search_jobs(
    request: JobSearchRequest,
    orchestrator: SearchOrchestrator = Depends(get_orchestrator),
    db: AsyncSession = Depends(get_db),
) -> SearchResponse:
    # If client_id is set, load config — resolve titles + merge defaults
    if request.client_id:
        request = await _resolve_client(request, db)

    # Final check: titles must exist by now
    if not request.titles:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No titles provided. Either pass 'titles' in request body or use 'client_id' with stored job_roles.",
        )

    return await orchestrator.execute(request)


async def _resolve_client(
    request: JobSearchRequest,
    db: AsyncSession,
) -> JobSearchRequest:
    """Resolve titles from client's job_roles and merge default filters."""
    result = await db.execute(
        select(ClientConfig).where(ClientConfig.client_id == request.client_id)
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client '{request.client_id}' not found",
        )

    # Resolve titles: request titles > client job_roles
    if not request.titles:
        if client.job_roles:
            request.titles = client.job_roles
            logger.info("[CLIENT] Using stored job_roles: %s", client.job_roles)
        else:
            logger.warning("[CLIENT] Client '%s' has no job_roles stored", request.client_id)

    # Merge source
    if request.source == SourceType.BOTH and client.default_source != "both":
        request.source = SourceType(client.default_source)

    # Merge shared filters
    if client.default_shared_filters:
        client_shared = SharedFilters(**client.default_shared_filters)
        request.filters = _merge_filters(request.filters, client_shared)

    # Merge ATS filters
    if client.default_ats_filters and not request.ats_filters:
        request.ats_filters = ATSFilters(**client.default_ats_filters)
    elif client.default_ats_filters and request.ats_filters:
        client_ats = ATSFilters(**client.default_ats_filters)
        request.ats_filters = _merge_filters(request.ats_filters, client_ats)

    # Merge LinkedIn filters
    if client.default_linkedin_filters and not request.linkedin_filters:
        request.linkedin_filters = LinkedInFilters(**client.default_linkedin_filters)
    elif client.default_linkedin_filters and request.linkedin_filters:
        client_li = LinkedInFilters(**client.default_linkedin_filters)
        request.linkedin_filters = _merge_filters(request.linkedin_filters, client_li)

    return request


def _merge_filters(request_filters, client_defaults):
    """Merge two filter objects. Request values win over client defaults."""
    request_data = request_filters.model_dump(exclude_unset=True)
    client_data = client_defaults.model_dump(exclude_none=True)
    merged = {**client_data, **request_data}
    return type(request_filters)(**merged)
