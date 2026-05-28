"""Normalize raw API responses from ATS and LinkedIn into a unified NormalizedJob schema."""

from app.schemas.response import NormalizedJob


def normalize_ats_job(raw: dict) -> NormalizedJob:
    """Map a single ATS API response record to NormalizedJob."""
    return NormalizedJob(
        id=str(raw.get("id", "")),
        title=(raw.get("title") or "").strip(),
        organization=raw.get("organization"),
        location=_first_or_none(raw.get("locations_derived")),
        url=raw.get("url"),
        source_api="ats",
        source_platform=raw.get("source"),
        date_posted=raw.get("date_posted"),
        date_indexed=raw.get("date_created"),
        is_expired=raw.get("is_expired"),
        # Location details
        city=_first_or_none(raw.get("cities_derived")),
        state=_first_or_none(raw.get("regions_derived")),
        country=_first_or_none(raw.get("countries_derived")),
        is_remote=raw.get("remote_derived"),
        # Description
        description_text=raw.get("description_text"),
        description_html=raw.get("description_html"),
        # Salary
        salary_raw=_stringify(raw.get("salary_raw")),
        ai_salary_min=_safe_float(raw.get("ai_salary_minvalue")),
        ai_salary_max=_safe_float(raw.get("ai_salary_maxvalue")),
        ai_salary_currency=raw.get("ai_salary_currency"),
        ai_salary_period=raw.get("ai_salary_unittext"),
        # AI enrichment
        ai_employment_type=_first_or_none(raw.get("ai_employment_type")),
        ai_taxonomy=_ensure_list(raw.get("ai_taxonomies_a")),
        ai_work_arrangement=raw.get("ai_work_arrangement"),
        ai_experience_level=raw.get("ai_experience_level"),
        ai_visa_sponsorship=raw.get("ai_visa_sponsorship"),
        ai_skills=_ensure_list(raw.get("ai_key_skills")),
        # LinkedIn company data
        li_company_slug=raw.get("linkedin_org_slug"),
        li_company_name=raw.get("organization"),
        li_industry=raw.get("linkedin_org_industry"),
        li_employee_count=_safe_int(raw.get("linkedin_org_employees")),
        li_company_description=raw.get("linkedin_org_description"),
        li_headquarters=raw.get("linkedin_org_headquarters"),
        li_followers=_safe_int(raw.get("linkedin_org_followers")),
        # Raw
        raw=raw,
    )


def normalize_linkedin_job(raw: dict) -> NormalizedJob:
    """Map a single LinkedIn API response record to NormalizedJob."""
    return NormalizedJob(
        id=str(raw.get("id", "")),
        title=(raw.get("title") or "").strip(),
        organization=raw.get("organization"),
        location=_first_or_none(raw.get("locations_derived")) or raw.get("location"),
        url=raw.get("url"),
        source_api="linkedin",
        source_platform="linkedin",
        date_posted=raw.get("date_posted"),
        date_indexed=raw.get("date_created"),
        is_expired=raw.get("is_expired"),
        # Location details
        city=_first_or_none(raw.get("cities_derived")),
        state=_first_or_none(raw.get("regions_derived")),
        country=_first_or_none(raw.get("countries_derived")),
        is_remote=raw.get("remote_derived"),
        # Description
        description_text=raw.get("description_text"),
        description_html=raw.get("description_html"),
        # Salary
        salary_raw=_stringify(raw.get("salary_raw")),
        ai_salary_min=_safe_float(raw.get("ai_salary_minvalue")),
        ai_salary_max=_safe_float(raw.get("ai_salary_maxvalue")),
        ai_salary_currency=raw.get("ai_salary_currency"),
        ai_salary_period=raw.get("ai_salary_unittext"),
        # AI enrichment
        ai_employment_type=_first_or_none(raw.get("ai_employment_type")),
        ai_taxonomy=_ensure_list(raw.get("ai_taxonomies_a")),
        ai_work_arrangement=raw.get("ai_work_arrangement"),
        ai_experience_level=raw.get("ai_experience_level"),
        ai_visa_sponsorship=raw.get("ai_visa_sponsorship"),
        ai_skills=_ensure_list(raw.get("ai_key_skills")),
        # LinkedIn company data
        li_company_slug=raw.get("linkedin_org_slug") or raw.get("organization_slug"),
        li_company_name=raw.get("organization"),
        li_industry=raw.get("linkedin_org_industry") or raw.get("industry"),
        li_employee_count=_safe_int(
            raw.get("linkedin_org_employees") or raw.get("organization_employees")
        ),
        li_company_description=raw.get("linkedin_org_description") or raw.get("organization_description"),
        li_headquarters=raw.get("linkedin_org_headquarters") or raw.get("organization_headquarters"),
        li_followers=_safe_int(
            raw.get("linkedin_org_followers") or raw.get("organization_followers")
        ),
        # Raw
        raw=raw,
    )


def normalize_ats_response(data: list[dict]) -> list[NormalizedJob]:
    return [normalize_ats_job(job) for job in data]


def normalize_linkedin_response(data: list[dict]) -> list[NormalizedJob]:
    return [normalize_linkedin_job(job) for job in data]


def deduplicate_jobs(jobs: list[NormalizedJob]) -> list[NormalizedJob]:
    """Deduplicate jobs by title + organization + location hash."""
    seen: set[str] = set()
    unique: list[NormalizedJob] = []
    for job in jobs:
        key = f"{(job.title or '').lower()}|{(job.organization or '').lower()}|{(job.location or '').lower()}"
        if key not in seen:
            seen.add(key)
            unique.append(job)
    return unique


def _safe_float(val) -> float | None:
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _safe_int(val) -> int | None:
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def _ensure_list(val) -> list:
    if val is None:
        return []
    if isinstance(val, list):
        return val
    return [val]


def _first_or_none(val) -> str | None:
    """Extract first element from a list, or return the value if it's a string."""
    if val is None:
        return None
    if isinstance(val, list):
        return val[0] if val else None
    return str(val)


def _stringify(val) -> str | None:
    """Convert any value to string, handling dicts/lists gracefully."""
    if val is None:
        return None
    if isinstance(val, str):
        return val
    if isinstance(val, dict):
        # salary_raw can be a MonetaryAmount dict
        parts = []
        if val.get("currency") or val.get("@currency"):
            parts.append(str(val.get("currency") or val.get("@currency", "")))
        if val.get("value"):
            v = val["value"]
            if isinstance(v, dict):
                min_v = v.get("minValue", "")
                max_v = v.get("maxValue", "")
                unit = v.get("unitText", "")
                parts.append(f"{min_v}-{max_v} {unit}".strip())
            else:
                parts.append(str(v))
        return " ".join(parts).strip() if parts else str(val)
    if isinstance(val, list):
        return ", ".join(str(v) for v in val)
    return str(val)
