# Fantastic Jobs API — Test Report

**Date:** March 28, 2026
**Platform:** macOS Darwin 25.1.0, Python 3.13.9
**Test Framework:** pytest 9.0.2 + pytest-asyncio 1.3.0
**Test DB:** SQLite (aiosqlite) — in-memory per test
**Total Tests:** 47 passed, 0 failed
**Execution Time:** 0.35 seconds
**External API Calls:** 0 (all mocked)
**Tokens Used:** 0 (no LLM calls in tests)
**Cost:** $0.00

---

## Summary

| Category | Tests | Status |
|---|---|---|
| Health Check | 1 | 1 passed |
| Client CRUD | 7 | 7 passed |
| Job Search (`/job-search`) | 10 | 10 passed |
| Legacy Search (`/search`) | 4 | 4 passed |
| ATS Normalizer | 5 | 5 passed |
| LinkedIn Normalizer | 3 | 3 passed |
| Deduplication | 3 | 3 passed |
| Query Builder (title filters) | 9 | 9 passed |
| Format Helpers | 5 | 5 passed |
| **Total** | **47** | **47 passed** |

---

## 1. Health Check (1 test)

### Test #1: `test_health_endpoint`
- **Request:** `GET /health`
- **Expected:** 200 OK with status and version
- **Response:**
```json
{"status": "ok", "version": "1.0.0", "services": ["fantastic-jobs", "job-title", "salary-estimator"]}
```
- **Result:** PASSED

---

## 2. Client CRUD Endpoints (7 tests)

### Test #2: `test_create_client`
- **Request:** `POST /api/v1/clients/`
```json
{"client_id": "acme", "client_name": "Acme Corp", "job_roles": ["Software Engineer", "Data Scientist"]}
```
- **Expected:** 201 Created
- **Response:**
```json
{"client_id": "acme", "client_name": "Acme Corp", "job_roles": ["Software Engineer", "Data Scientist"], "default_source": "both", "default_shared_filters": {}, ...}
```
- **Result:** PASSED

### Test #3: `test_create_duplicate_client`
- **Request:** `POST /api/v1/clients/` (same client_id twice)
- **Expected:** 409 Conflict
- **Response:** `{"detail": "Client 'acme' already exists"}`
- **Result:** PASSED

### Test #4: `test_get_client`
- **Request:** `GET /api/v1/clients/acme`
- **Expected:** 200 OK with full client config
- **Response:** `{"client_id": "acme", ...}`
- **Result:** PASSED

### Test #5: `test_get_nonexistent_client`
- **Request:** `GET /api/v1/clients/nope`
- **Expected:** 404 Not Found
- **Response:** `{"detail": "Client 'nope' not found"}`
- **Result:** PASSED

### Test #6: `test_update_client`
- **Request:** `PUT /api/v1/clients/acme`
```json
{"client_name": "Acme Inc", "job_roles": ["Developer", "Designer"]}
```
- **Expected:** 200 OK with updated fields
- **Response:** `{"client_name": "Acme Inc", "job_roles": ["Developer", "Designer"], ...}`
- **Result:** PASSED

### Test #7: `test_delete_client`
- **Request:** `DELETE /api/v1/clients/acme`
- **Expected:** 204 No Content, then GET returns 404
- **Result:** PASSED

### Test #8: `test_delete_nonexistent_client`
- **Request:** `DELETE /api/v1/clients/nope`
- **Expected:** 404 Not Found
- **Result:** PASSED

---

## 3. Job Search Endpoint — POST /api/v1/job-search (10 tests)

> All external API calls are mocked. No real RapidAPI requests made.

### Test #9: `test_linkedin_search`
- **Request:**
```json
{"type": "LINKEDIN", "advanced_title_filter": ["Program Manager", "Salesforce Consultant"], "limit": 10, "include_ai": true}
```
- **Mock API returns:** 2 jobs (Program Manager @ Google, Salesforce Consultant @ Deloitte)
- **Response:**
```json
{"sources_queried": ["linkedin"], "total_results": 2, "jobs": [{"title": "Program Manager", "source_api": "linkedin", ...}, ...]}
```
- **Assertions:** status=200, sources=["linkedin"], total=2, first job title="Program Manager", source_api="linkedin"
- **Result:** PASSED

### Test #10: `test_ats_search`
- **Request:**
```json
{"type": "ATS_CAREER_SITES", "advanced_title_filter": ["Business Architect"], "limit": 15}
```
- **Mock API returns:** 1 job (Business Architect @ Acme via greenhouse)
- **Response:**
```json
{"sources_queried": ["ats"], "total_results": 1, "jobs": [{"source_api": "ats", ...}]}
```
- **Assertions:** status=200, sources=["ats"], total=1, source_api="ats"
- **Result:** PASSED

### Test #11: `test_search_with_all_filters`
- **Request:**
```json
{
  "type": "LINKEDIN",
  "advanced_title_filter": ["Program Manager"],
  "limit": 10,
  "location_filter": ["Atlanta", "Seattle", "Dallas"],
  "type_filter": "CONTRACTOR",
  "remote": true,
  "agency": true,
  "industry_filter": "Technology",
  "date_filter": "2025-01-01",
  "exclude_ats_duplicate": true,
  "include_ai": true
}
```
- **Mock API returns:** empty list (0 jobs)
- **Assertions:** status=200, total=0 (all filters accepted without error)
- **Result:** PASSED

### Test #12: `test_missing_type_returns_422`
- **Request:** `{"advanced_title_filter": ["Engineer"]}` (no `type` field)
- **Expected:** 422 Validation Error
- **Result:** PASSED

### Test #13: `test_missing_titles_returns_422`
- **Request:** `{"type": "LINKEDIN"}` (no `advanced_title_filter`)
- **Expected:** 422 Validation Error
- **Result:** PASSED

### Test #14: `test_empty_titles_returns_422`
- **Request:** `{"type": "LINKEDIN", "advanced_title_filter": []}`
- **Expected:** 422 (min_length=1 violated)
- **Result:** PASSED

### Test #15: `test_invalid_type_returns_422`
- **Request:** `{"type": "INVALID", "advanced_title_filter": ["Engineer"]}`
- **Expected:** 422 (not a valid JobType enum)
- **Result:** PASSED

### Test #16: `test_invalid_type_filter_returns_422`
- **Request:** `{"type": "LINKEDIN", "advanced_title_filter": ["Engineer"], "type_filter": "INVALID_TYPE"}`
- **Expected:** 422 (not a valid TypeFilter enum)
- **Result:** PASSED

### Test #17: `test_response_has_metadata`
- **Request:** `{"type": "ATS_CAREER_SITES", "advanced_title_filter": ["Engineer"]}`
- **Mock API returns:** 1 job
- **Assertions:** response has `metadata.elapsed_seconds`, `page=1`, `page_size=10`
- **Result:** PASSED

### Test #18: `test_dict_response_format`
- **Request:** `{"type": "LINKEDIN", "advanced_title_filter": ["PM"]}`
- **Mock API returns:** `{"data": [{"id": "1", "title": "PM", "organization": "X"}]}` (dict format instead of list)
- **Assertions:** status=200, total=1 (correctly extracts jobs from `data` key)
- **Result:** PASSED

---

## 4. Legacy Search Endpoint — POST /api/v1/search (4 tests)

### Test #19: `test_search_with_titles`
- **Request:**
```json
{"titles": ["Software Engineer"], "source": "ats"}
```
- **Mock:** ATSClient and LinkedInClient mocked at orchestrator level
- **Assertions:** status=200, sources_queried=["ats"], jobs returned
- **Result:** PASSED

### Test #20: `test_search_without_titles_or_client`
- **Request:** `{"source": "ats"}` (no titles, no client_id)
- **Expected:** 422 — "No titles provided"
- **Result:** PASSED

### Test #21: `test_search_with_nonexistent_client`
- **Request:** `{"client_id": "no-such-client"}`
- **Expected:** 404 — "Client 'no-such-client' not found"
- **Result:** PASSED

### Test #22: `test_search_title_filter_mutual_exclusion`
- **Request:** `{"titles": ["Engineer"], "title_filter": "foo", "advanced_title_filter": "bar"}`
- **Expected:** 422 — "Cannot use both title_filter and advanced_title_filter"
- **Result:** PASSED

---

## 5. ATS Normalizer (5 tests)

### Test #23: `test_basic_fields`
- **Input:** Raw ATS API response with id="ats-123", title="Software Engineer", organization="Acme Corp", source="greenhouse"
- **Output:** NormalizedJob with source_api="ats", source_platform="greenhouse", location="San Francisco, CA"
- **Result:** PASSED

### Test #24: `test_salary_fields`
- **Input:** ai_salary_minvalue=100000, ai_salary_maxvalue=150000, ai_salary_currency="USD"
- **Output:** ai_salary_min=100000.0, ai_salary_max=150000.0, ai_salary_currency="USD"
- **Result:** PASSED

### Test #25: `test_ai_enrichment`
- **Input:** ai_employment_type=["FULL_TIME"], ai_key_skills=["Python", "FastAPI"], ai_taxonomies_a=["Technology"]
- **Output:** ai_employment_type="FULL_TIME", ai_skills=["Python", "FastAPI"], ai_taxonomy=["Technology"]
- **Result:** PASSED

### Test #26: `test_title_strip_whitespace`
- **Input:** title="  Engineer  "
- **Output:** title="Engineer" (stripped)
- **Result:** PASSED

### Test #27: `test_missing_optional_fields`
- **Input:** `{"id": "1", "title": "Test"}` (minimal — no salary, no skills, no org)
- **Output:** organization=None, ai_salary_min=None, ai_skills=[] (graceful defaults)
- **Result:** PASSED

---

## 6. LinkedIn Normalizer (3 tests)

### Test #28: `test_basic_fields`
- **Input:** Raw LinkedIn API response with id="li-456", title="Data Scientist"
- **Output:** source_api="linkedin", source_platform="linkedin"
- **Result:** PASSED

### Test #29: `test_linkedin_company_fields`
- **Input:** organization_slug="bigco", industry="Technology", organization_employees=5000
- **Output:** li_company_slug="bigco", li_industry="Technology", li_employee_count=5000
- **Result:** PASSED

### Test #30: `test_fallback_location`
- **Input:** locations_derived=None, location="Remote"
- **Output:** location="Remote" (falls back to `location` field when `locations_derived` is empty)
- **Result:** PASSED

---

## 7. Deduplication (3 tests)

### Test #31: `test_removes_duplicates`
- **Input:** 2 jobs from different sources but same title="Software Engineer", org="Acme Corp", location="San Francisco, CA"
- **Output:** 1 job (duplicate removed by title+org+location hash)
- **Result:** PASSED

### Test #32: `test_keeps_unique_jobs`
- **Input:** 2 jobs with different titles (Software Engineer vs Data Scientist)
- **Output:** 2 jobs (both kept)
- **Result:** PASSED

### Test #33: `test_empty_list`
- **Input:** empty list
- **Output:** empty list
- **Result:** PASSED

---

## 8. Query Builder — Title Filters (9 tests)

### Test #34: `test_single_simple_title`
- **Input:** `["Software Engineer"]`
- **Output:** title_filter=`"Software Engineer"`, advanced_title_filter=None
- **Result:** PASSED

### Test #35: `test_single_complex_title_with_special_chars`
- **Input:** `["Engineer/Developer"]`
- **Output:** title_filter=`"Engineer/Developer"` (special char `/` detected, still uses title_filter)
- **Result:** PASSED

### Test #36: `test_multiple_titles_builds_advanced_filter`
- **Input:** `["Software Engineer", "Backend Developer"]`
- **Output:** title_filter=None, advanced_title_filter=`'Software Engineer' | 'Backend Developer'`
- **Result:** PASSED

### Test #37: `test_multiple_titles_single_word`
- **Input:** `["Engineer", "Developer"]`
- **Output:** advanced_title_filter=`Engineer | Developer` (no quotes for single-word titles)
- **Result:** PASSED

### Test #38: `test_multiple_titles_mixed`
- **Input:** `["Engineer", "Backend Developer"]`
- **Output:** advanced_title_filter=`Engineer | 'Backend Developer'` (single-word unquoted, multi-word quoted)
- **Result:** PASSED

### Test #39: `test_title_filter_override`
- **Input:** titles=["ignored"], title_filter_override="my custom filter"
- **Output:** title_filter="my custom filter" (override wins)
- **Result:** PASSED

### Test #40: `test_advanced_title_filter_override`
- **Input:** titles=["ignored"], advanced_title_filter_override="foo | bar & baz"
- **Output:** advanced_title_filter="foo | bar & baz" (override wins)
- **Result:** PASSED

### Test #41: `test_advanced_override_takes_precedence`
- **Input:** both overrides set: title_filter_override="simple", advanced_title_filter_override="complex"
- **Output:** advanced_title_filter="complex" (advanced wins over simple)
- **Result:** PASSED

### Test #42: `test_empty_titles_in_list_are_skipped`
- **Input:** `["Engineer", "", "Developer"]`
- **Output:** advanced_title_filter contains "Engineer" and "Developer" (empty string skipped)
- **Result:** PASSED

---

## 9. Format Helpers (5 tests)

### Test #43: `test_basic` (comma list)
- **Input:** `["a", "b", "c"]`
- **Output:** `"a,b,c"`
- **Result:** PASSED

### Test #44: `test_strips_whitespace`
- **Input:** `[" a ", " b "]`
- **Output:** `"a,b"`
- **Result:** PASSED

### Test #45: `test_skips_empty`
- **Input:** `["a", "", "b"]`
- **Output:** `"a,b"`
- **Result:** PASSED

### Test #46: `test_basic` (taxonomy list)
- **Input:** `["Tech", "Finance"]`
- **Output:** `"Tech,Finance"`
- **Result:** PASSED

### Test #47: `test_quotes_ampersand`
- **Input:** `["Science & Tech", "Finance"]`
- **Output:** `'"Science & Tech",Finance'` (ampersand items double-quoted per API requirement)
- **Result:** PASSED

---

## Cost Analysis

### Test Execution Cost

| Resource | Usage | Cost |
|---|---|---|
| RapidAPI (ATS/LinkedIn) | 0 calls (mocked) | $0.00 |
| Groq LLM (Job Titles) | 0 calls (mocked) | $0.00 |
| SerpAPI (Salary Search) | 0 calls (mocked) | $0.00 |
| HuggingFace (Salary LLM) | 0 calls (mocked) | $0.00 |
| Database | SQLite in-memory | $0.00 |
| **Total Test Cost** | | **$0.00** |

### Why $0: All external APIs are mocked in tests. No real HTTP requests are made. The test suite uses:
- `unittest.mock.patch` to mock API client methods
- `aiosqlite` for a local test database (created/destroyed per test)
- `httpx.ASGITransport` for in-process HTTP testing (no server needed)

### Production API Cost Estimates (per request)

| Service | External API | Cost per Call |
|---|---|---|
| Fantastic Jobs | RapidAPI ATS | $2.50/1K jobs (Pro) |
| Fantastic Jobs | RapidAPI LinkedIn | $1.25/1K jobs (Pro) |
| Job Title | Groq (llama-3.3-70b) | ~$0.001/request (~2K tokens) |
| Salary Estimator | SerpAPI | $0.01/search (4-5 searches/job) |
| Salary Estimator | HuggingFace | ~$0.001/request (~500 tokens) |

### Token Estimates (per request, production)

| Service | Prompt Tokens | Completion Tokens | Total |
|---|---|---|---|
| Job Title (Groq) | ~1,500-3,000 | ~500-1,000 | ~2,000-4,000 |
| Salary Estimator (HF) | ~800-1,200 | ~100-300 | ~900-1,500 |

---

## Test Infrastructure

```
Test DB:        SQLite + aiosqlite (in-memory, per-test lifecycle)
Test Client:    httpx.AsyncClient with ASGITransport
Mocking:        unittest.mock.patch + AsyncMock
Fixtures:       pytest-asyncio fixtures in conftest.py
Isolation:      Tables created before each test, dropped after
```

---

## Warnings (non-blocking)

1. **PyPDF2 deprecation** — `PyPDF2 is deprecated. Please move to the pypdf library instead.`
2. **FastAPI status code** — `HTTP_422_UNPROCESSABLE_ENTITY is deprecated. Use HTTP_422_UNPROCESSABLE_CONTENT`

Neither affects functionality.
