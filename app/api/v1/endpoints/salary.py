"""Salary estimation endpoint — POST /api/v1/estimate-salary."""

import asyncio
import logging

import httpx
from fastapi import APIRouter, Request

from app.core.config import get_settings
from app.schemas.salary import (
    SalaryRange,
    SalaryRequest,
    SalaryResponse,
    SalaryResult,
)
from app.services.salary_estimator.confidence_service import calculate_confidence
from app.services.salary_estimator.llm_service import extract_salary_with_llm
from app.services.salary_estimator.search_service import search_salary_data
from app.utils.salary_parser import extract_salaries

logger = logging.getLogger("app.salary_estimator")

router = APIRouter(tags=["salary-estimator"])


def _format_usd(val: int | float | None) -> str | None:
    if val is None:
        return None
    if val >= 1000:
        return f"${round(val / 1000)}k/yr"
    return f"${val}/yr"


def _clamp_salary(val: int | float | None, floor: float, ceiling: float) -> int | float | None:
    if val is None:
        return None
    return max(floor, min(ceiling, val))


def _get_exp_salary_bounds(years_of_experience: str | None) -> tuple[float, float]:
    if years_of_experience is None:
        return (20_000, 600_000)
    try:
        years = int(years_of_experience)
    except (ValueError, TypeError):
        return (20_000, 600_000)

    if years <= 2:
        return (30_000, 250_000)
    elif years <= 5:
        return (50_000, 400_000)
    elif years <= 10:
        return (70_000, 550_000)
    elif years <= 15:
        return (90_000, 700_000)
    else:
        return (100_000, 800_000)


async def _process_job(http_client: httpx.AsyncClient, job_data: dict, serp_api_key: str) -> SalaryResult:
    company = job_data["companyName"]
    designation = job_data["designation"]
    experience = job_data.get("yearsOfExperience")
    location = job_data["location"]

    logger.info(">> PROCESSING: %s, %s, exp=%s, loc=%s", company, designation, experience, location)

    # Step 1: Search
    search_results = await search_salary_data(http_client, company, designation, experience, location, serp_api_key)

    if not search_results:
        return SalaryResult(
            companyName=company, designation=designation,
            yearsOfExperience=experience, location=location,
            error="No relevant search results found",
        )

    # Step 2: Extract salary with LLM (fallback to regex)
    extraction = await extract_salary_with_llm(
        http_client, company, designation, experience, location, search_results,
    )

    # Step 3: Calculate confidence
    all_snippet_text = " ".join(f"{r['title']} {r['snippet']}" for r in search_results)
    regex_values = extract_salaries(all_snippet_text)
    trusted_count = sum(1 for r in search_results if r["is_trusted"])
    confidence_score = calculate_confidence(
        sources_count=len(extraction["sources"]) or trusted_count,
        salary_values=regex_values if regex_values else ([extraction["estimated"]] if extraction["estimated"] else []),
        company_name=company,
        location=location,
        has_experience=bool(experience),
        search_results=search_results,
    )

    # Step 4: Clamp salary
    floor, ceiling = _get_exp_salary_bounds(experience)
    estimated = _clamp_salary(extraction["estimated"], floor, ceiling)
    lower = _clamp_salary(extraction["lower"], floor, ceiling)
    upper = _clamp_salary(extraction["upper"], floor, ceiling)

    # Step 5: Build result
    estimated_salary = _format_usd(estimated)
    salary_range = None
    if estimated:
        salary_range = SalaryRange(lower=_format_usd(lower), upper=_format_usd(upper))

    unique_sources = list(dict.fromkeys(extraction["sources"]))

    logger.info(">> RESULT: %s at %s -> %s (confidence=%.2f)", designation, company, estimated_salary, confidence_score)

    return SalaryResult(
        companyName=company, designation=designation,
        yearsOfExperience=experience, location=location,
        estimatedSalary=estimated_salary, salaryRange=salary_range,
        confidenceScore=confidence_score, sources=unique_sources,
    )


@router.post("/estimate-salary", response_model=SalaryResponse, summary="Estimate salary for job positions")
async def estimate_salaries(request: Request, body: SalaryRequest):
    settings = get_settings()

    if len(body.jobs) > settings.MAX_BATCH_SIZE:
        return SalaryResponse(success=False, count=0, results=[], trace_id=None)

    logger.info(">> REQUEST received: %d job(s)", len(body.jobs))

    # Use app-level http client if available, else create one
    http_client = getattr(request.app.state, "http_client", None)
    should_close = False
    if http_client is None:
        http_client = httpx.AsyncClient(
            limits=httpx.Limits(max_connections=20),
            timeout=httpx.Timeout(30),
        )
        should_close = True

    try:
        semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_SEARCHES)

        async def limited_process(job):
            async with semaphore:
                return await _process_job(http_client, job.model_dump(), body.serpApiKey)

        tasks = [limited_process(job) for job in body.jobs]
        raw_results = await asyncio.gather(*tasks, return_exceptions=True)

        results: list[SalaryResult] = []
        for i, result in enumerate(raw_results):
            if isinstance(result, Exception):
                logger.error(">> Job %d failed: %s", i, str(result))
                job = body.jobs[i]
                results.append(SalaryResult(
                    companyName=job.companyName, designation=job.designation,
                    yearsOfExperience=job.yearsOfExperience, location=job.location,
                    error="Failed to estimate salary",
                ))
            else:
                results.append(result)

        logger.info(">> RESPONSE: %d result(s) ready", len(results))
        return SalaryResponse(success=True, count=len(results), results=results)
    finally:
        if should_close:
            await http_client.aclose()
