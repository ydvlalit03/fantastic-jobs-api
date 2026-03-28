"""Tests for the normalizer service."""

from app.services.fantastic_jobs.normalizer import (
    deduplicate_jobs,
    normalize_ats_job,
    normalize_linkedin_job,
)


def _make_raw_ats_job(**overrides):
    base = {
        "id": "ats-123",
        "title": "Software Engineer",
        "organization": "Acme Corp",
        "url": "https://acme.com/jobs/123",
        "source": "greenhouse",
        "locations_derived": ["San Francisco, CA"],
        "cities_derived": ["San Francisco"],
        "regions_derived": ["California"],
        "countries_derived": ["United States"],
        "remote_derived": False,
        "date_posted": "2025-01-01",
        "date_created": "2025-01-02",
        "is_expired": False,
        "description_text": "Build things.",
        "description_html": "<p>Build things.</p>",
        "salary_raw": None,
        "ai_salary_minvalue": 100000,
        "ai_salary_maxvalue": 150000,
        "ai_salary_currency": "USD",
        "ai_salary_unittext": "YEAR",
        "ai_employment_type": ["FULL_TIME"],
        "ai_taxonomies_a": ["Technology"],
        "ai_work_arrangement": "Remote OK",
        "ai_experience_level": "2-5",
        "ai_visa_sponsorship": True,
        "ai_key_skills": ["Python", "FastAPI"],
    }
    base.update(overrides)
    return base


def _make_raw_linkedin_job(**overrides):
    base = {
        "id": "li-456",
        "title": "Data Scientist",
        "organization": "BigCo",
        "url": "https://linkedin.com/jobs/456",
        "locations_derived": ["New York, NY"],
        "cities_derived": ["New York"],
        "regions_derived": ["New York"],
        "countries_derived": ["United States"],
        "remote_derived": True,
        "date_posted": "2025-02-01",
        "date_created": "2025-02-02",
        "is_expired": False,
        "description_text": "Analyze data.",
        "ai_employment_type": ["FULL_TIME"],
        "ai_taxonomies_a": ["Data Science"],
        "organization_slug": "bigco",
        "industry": "Technology",
        "organization_employees": 5000,
    }
    base.update(overrides)
    return base


class TestNormalizeATSJob:
    def test_basic_fields(self):
        job = normalize_ats_job(_make_raw_ats_job())
        assert job.id == "ats-123"
        assert job.title == "Software Engineer"
        assert job.organization == "Acme Corp"
        assert job.source_api == "ats"
        assert job.source_platform == "greenhouse"
        assert job.location == "San Francisco, CA"

    def test_salary_fields(self):
        job = normalize_ats_job(_make_raw_ats_job())
        assert job.ai_salary_min == 100000.0
        assert job.ai_salary_max == 150000.0
        assert job.ai_salary_currency == "USD"

    def test_ai_enrichment(self):
        job = normalize_ats_job(_make_raw_ats_job())
        assert job.ai_employment_type == "FULL_TIME"
        assert job.ai_skills == ["Python", "FastAPI"]
        assert job.ai_taxonomy == ["Technology"]

    def test_title_strip_whitespace(self):
        job = normalize_ats_job(_make_raw_ats_job(title="  Engineer  "))
        assert job.title == "Engineer"

    def test_missing_optional_fields(self):
        job = normalize_ats_job({"id": "1", "title": "Test"})
        assert job.id == "1"
        assert job.title == "Test"
        assert job.organization is None
        assert job.ai_salary_min is None
        assert job.ai_skills == []


class TestNormalizeLinkedInJob:
    def test_basic_fields(self):
        job = normalize_linkedin_job(_make_raw_linkedin_job())
        assert job.id == "li-456"
        assert job.title == "Data Scientist"
        assert job.source_api == "linkedin"
        assert job.source_platform == "linkedin"

    def test_linkedin_company_fields(self):
        job = normalize_linkedin_job(_make_raw_linkedin_job())
        assert job.li_company_slug == "bigco"
        assert job.li_industry == "Technology"
        assert job.li_employee_count == 5000

    def test_fallback_location(self):
        raw = _make_raw_linkedin_job(locations_derived=None, location="Remote")
        job = normalize_linkedin_job(raw)
        assert job.location == "Remote"


class TestDeduplicateJobs:
    def test_removes_duplicates(self):
        job1 = normalize_ats_job(_make_raw_ats_job())
        job2 = normalize_linkedin_job(
            _make_raw_linkedin_job(
                title="Software Engineer",
                organization="Acme Corp",
                locations_derived=["San Francisco, CA"],
            )
        )
        result = deduplicate_jobs([job1, job2])
        assert len(result) == 1

    def test_keeps_unique_jobs(self):
        job1 = normalize_ats_job(_make_raw_ats_job())
        job2 = normalize_linkedin_job(_make_raw_linkedin_job())
        result = deduplicate_jobs([job1, job2])
        assert len(result) == 2

    def test_empty_list(self):
        assert deduplicate_jobs([]) == []
