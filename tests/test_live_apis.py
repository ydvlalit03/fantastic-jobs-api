"""Live API tests — hits real external APIs. Run with: pytest tests/test_live_apis.py -v -s"""

import os
import time

import httpx
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Force SQLite for tests
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///test_live.db"

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

engine = create_async_engine("sqlite+aiosqlite:///test_live.db", echo=False)
TestSession = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    async def override_get_db():
        async with TestSession() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ═══════════════════════════════════════════════════════════════════
# TEST 1: Health Check
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_01_health(client):
    """Health check — all 3 services listed."""
    t0 = time.time()
    resp = await client.get("/health")
    elapsed = time.time() - t0

    print(f"\n{'='*60}")
    print(f"TEST 1: GET /health")
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.json()}")
    print(f"Time: {elapsed:.3f}s")
    print(f"{'='*60}")

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "fantastic-jobs" in data["services"]
    assert "job-title" in data["services"]
    assert "salary-estimator" in data["services"]


# ═══════════════════════════════════════════════════════════════════
# TEST 2: Client Onboarding
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_02_client_onboard(client):
    """Onboard a new client with job_roles and default filters."""
    payload = {
        "client_id": "leadfreak",
        "client_name": "LeadFreak",
        "job_roles": ["Data Engineer", "ML Engineer", "Backend Developer"],
        "default_shared_filters": {
            "remote": True,
            "include_ai": True,
        },
    }

    t0 = time.time()
    resp = await client.post("/api/v1/clients/", json=payload)
    elapsed = time.time() - t0

    print(f"\n{'='*60}")
    print(f"TEST 2: POST /api/v1/clients/")
    print(f"Request: {payload}")
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.json()}")
    print(f"Time: {elapsed:.3f}s")
    print(f"{'='*60}")

    assert resp.status_code == 201
    data = resp.json()
    assert data["client_id"] == "leadfreak"
    assert data["job_roles"] == ["Data Engineer", "ML Engineer", "Backend Developer"]


# ═══════════════════════════════════════════════════════════════════
# TEST 3: Job Search — LinkedIn (LIVE API)
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_03_job_search_linkedin(client):
    """Search LinkedIn for Software Engineer jobs — LIVE RapidAPI call."""
    payload = {
        "type": "LINKEDIN",
        "advanced_title_filter": ["Software Engineer"],
        "limit": 5,
        "location_filter": ["San Francisco"],
        "include_ai": True,
    }

    t0 = time.time()
    resp = await client.post("/api/v1/job-search", json=payload)
    elapsed = time.time() - t0

    print(f"\n{'='*60}")
    print(f"TEST 3: POST /api/v1/job-search (LINKEDIN — LIVE)")
    print(f"Request: {payload}")
    print(f"Status: {resp.status_code}")
    print(f"Time: {elapsed:.3f}s")

    if resp.status_code == 200:
        data = resp.json()
        print(f"Total Results: {data['total_results']}")
        print(f"Sources: {data['sources_queried']}")
        print(f"Has More: {data['has_more']}")
        print(f"Metadata: {data['metadata']}")
        print(f"\nJobs:")
        for i, job in enumerate(data["jobs"][:5]):
            print(f"  {i+1}. {job['title']} @ {job['organization']}")
            print(f"     Location: {job['location']} | Remote: {job.get('is_remote')}")
            print(f"     Source: {job['source_api']}/{job.get('source_platform')}")
            print(f"     URL: {job.get('url', 'N/A')}")
            if job.get("ai_salary_min"):
                print(f"     Salary: ${job['ai_salary_min']:,.0f} - ${job['ai_salary_max']:,.0f} {job.get('ai_salary_currency', '')}")
            if job.get("ai_employment_type"):
                print(f"     Type: {job['ai_employment_type']} | Arrangement: {job.get('ai_work_arrangement')}")
    else:
        print(f"Error: {resp.text}")

    print(f"{'='*60}")
    assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════════════
# TEST 4: Job Search — ATS Career Sites (LIVE API)
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_04_job_search_ats(client):
    """Search ATS for Data Engineer jobs — LIVE RapidAPI call."""
    payload = {
        "type": "ATS_CAREER_SITES",
        "advanced_title_filter": ["Data Engineer", "ML Engineer"],
        "limit": 5,
        "remote": True,
        "include_ai": True,
    }

    t0 = time.time()
    resp = await client.post("/api/v1/job-search", json=payload)
    elapsed = time.time() - t0

    print(f"\n{'='*60}")
    print(f"TEST 4: POST /api/v1/job-search (ATS_CAREER_SITES — LIVE)")
    print(f"Request: {payload}")
    print(f"Status: {resp.status_code}")
    print(f"Time: {elapsed:.3f}s")

    if resp.status_code == 200:
        data = resp.json()
        print(f"Total Results: {data['total_results']}")
        print(f"Sources: {data['sources_queried']}")
        print(f"\nJobs:")
        for i, job in enumerate(data["jobs"][:5]):
            print(f"  {i+1}. {job['title']} @ {job['organization']}")
            print(f"     Location: {job['location']} | Remote: {job.get('is_remote')}")
            print(f"     Platform: {job.get('source_platform')}")
            print(f"     URL: {job.get('url', 'N/A')}")
            if job.get("ai_salary_min"):
                print(f"     Salary: ${job['ai_salary_min']:,.0f} - ${job['ai_salary_max']:,.0f} {job.get('ai_salary_currency', '')}")
            if job.get("ai_skills"):
                print(f"     Skills: {', '.join(job['ai_skills'][:5])}")
    else:
        print(f"Error: {resp.text}")

    print(f"{'='*60}")
    assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════════════
# TEST 5: Job Search — Multiple titles with location filter
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_05_job_search_multi_title(client):
    """Search with multiple titles and contractor filter — LIVE."""
    payload = {
        "type": "LINKEDIN",
        "advanced_title_filter": ["Program Manager", "Product Manager", "Scrum Master"],
        "limit": 5,
        "location_filter": ["New York", "Boston"],
        "type_filter": "FULL_TIME",
        "include_ai": True,
    }

    t0 = time.time()
    resp = await client.post("/api/v1/job-search", json=payload)
    elapsed = time.time() - t0

    print(f"\n{'='*60}")
    print(f"TEST 5: POST /api/v1/job-search (Multi-title + Location — LIVE)")
    print(f"Request: {payload}")
    print(f"Status: {resp.status_code}")
    print(f"Time: {elapsed:.3f}s")

    if resp.status_code == 200:
        data = resp.json()
        print(f"Total Results: {data['total_results']}")
        print(f"Filter used: {data['metadata'].get('advanced_title_filter_used')}")
        print(f"\nJobs:")
        for i, job in enumerate(data["jobs"][:5]):
            print(f"  {i+1}. {job['title']} @ {job['organization']}")
            print(f"     Location: {job['location']}")
            if job.get("li_employee_count"):
                print(f"     Company Size: {job['li_employee_count']:,} employees")
    else:
        print(f"Error: {resp.text}")

    print(f"{'='*60}")
    assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════════════
# TEST 6: Validation — missing required fields
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_06_validation_errors(client):
    """Validation errors for bad requests."""
    test_cases = [
        ("No type", {"advanced_title_filter": ["Engineer"]}),
        ("No titles", {"type": "LINKEDIN"}),
        ("Empty titles", {"type": "LINKEDIN", "advanced_title_filter": []}),
        ("Invalid type", {"type": "GOOGLE", "advanced_title_filter": ["PM"]}),
    ]

    print(f"\n{'='*60}")
    print(f"TEST 6: Validation Errors")

    for name, payload in test_cases:
        resp = await client.post("/api/v1/job-search", json=payload)
        status = "PASS" if resp.status_code == 422 else "FAIL"
        print(f"  [{status}] {name}: status={resp.status_code}")
        assert resp.status_code == 422

    print(f"{'='*60}")
