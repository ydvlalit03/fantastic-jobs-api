# Fantastic Jobs API — Live Test Report

**Date:** March 28, 2026
**Total Tests:** 6 passed, 0 failed
**Execution Time:** 4.94 seconds
**Real API Calls:** 3 (RapidAPI LinkedIn x2, RapidAPI ATS x1)
**Tokens Used:** 0 (no LLM tests — Groq/HF not tested due to file upload requirement & missing SerpAPI key)

---

## Results Summary

| # | Test | Endpoint | Status | Time | API Calls |
|---|---|---|---|---|---|
| 1 | Health Check | GET /health | 200 | 0.002s | 0 |
| 2 | Client Onboarding | POST /api/v1/clients/ | 201 | 0.011s | 0 |
| 3 | LinkedIn Job Search | POST /api/v1/job-search | 200 | 1.64s | 1 (RapidAPI LinkedIn) |
| 4 | ATS Job Search | POST /api/v1/job-search | 200 | 1.58s | 1 (RapidAPI ATS) |
| 5 | Multi-title + Location | POST /api/v1/job-search | 200 | 1.63s | 1 (RapidAPI LinkedIn) |
| 6 | Validation Errors (4 cases) | POST /api/v1/job-search | 422 x4 | <0.01s | 0 |

---

## Test 1: Health Check

```
GET /health
```

**Response (200 OK, 0.002s):**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "services": ["fantastic-jobs", "job-title", "salary-estimator"]
}
```

---

## Test 2: Client Onboarding

```
POST /api/v1/clients/
```

**Request:**
```json
{
  "client_id": "leadfreak",
  "client_name": "LeadFreak",
  "job_roles": ["Data Engineer", "ML Engineer", "Backend Developer"],
  "default_shared_filters": {"remote": true, "include_ai": true}
}
```

**Response (201 Created, 0.011s):**
```json
{
  "id": 1,
  "client_id": "leadfreak",
  "client_name": "LeadFreak",
  "job_roles": ["Data Engineer", "ML Engineer", "Backend Developer"],
  "default_source": "both",
  "default_shared_filters": {"description_type": "text", "remote": true, "include_ai": true, "include_li": true},
  "default_ats_filters": null,
  "default_linkedin_filters": null,
  "created_at": "2026-03-28T19:40:34",
  "updated_at": "2026-03-28T19:40:34"
}
```

---

## Test 3: LinkedIn Job Search (LIVE)

```
POST /api/v1/job-search
```

**Request:**
```json
{
  "type": "LINKEDIN",
  "advanced_title_filter": ["Software Engineer"],
  "limit": 5,
  "location_filter": ["San Francisco"],
  "include_ai": true
}
```

**Query sent to RapidAPI:**
```
GET https://linkedin-job-search-api.p.rapidapi.com/active-jb-7d
  ?limit=5&offset=0
  &title_filter="Software Engineer"
  &location_filter="San Francisco"
  &include_ai=true
```

**Response (200 OK, 1.64s, 5 jobs):**

| # | Title | Company | Location | Salary | URL |
|---|---|---|---|---|---|
| 1 | Staff Software Engineer, Data Platform (FedRamp) | Okta | San Francisco, CA | $194,000 - $267,000 | [linkedin](https://www.linkedin.com/jobs/view/staff-software-engineer-data-platform-fedramp-at-okta-4380825405) |
| 2 | Software Engineer, Travel, Juno | Ramp | San Francisco, CA | $204,000 - $280,000 | [linkedin](https://www.linkedin.com/jobs/view/software-engineer-travel-juno-at-ramp-4392095309) |
| 3 | Software Engineer Intern - Summer 2026 | Novaflow (YC S25) | San Francisco, CA | $6,000 - $10,000 | [linkedin](https://www.linkedin.com/jobs/view/software-engineer-intern-summer-2026-at-novaflow-yc-s25-4391608719) |
| 4 | Staff Software Engineer Storage, Search, & Data Platforms | Uber | San Francisco, CA | $232,000 - $258,000 | [linkedin](https://www.linkedin.com/jobs/view/staff-software-engineer-storage-search-data-platforms-at-uber-4392059524) |
| 5 | Senior Software Engineer | VetScribe | San Francisco, CA | — | [linkedin](https://www.linkedin.com/jobs/view/senior-software-engineer-at-vetscribe-4391254135) |

**Metadata:**
```json
{"elapsed_seconds": 1.635, "title_filter_used": "\"Software Engineer\"", "advanced_title_filter_used": null, "errors": null}
```

---

## Test 4: ATS Career Sites Job Search (LIVE)

```
POST /api/v1/job-search
```

**Request:**
```json
{
  "type": "ATS_CAREER_SITES",
  "advanced_title_filter": ["Data Engineer", "ML Engineer"],
  "limit": 5,
  "remote": true,
  "include_ai": true
}
```

**Query sent to RapidAPI:**
```
GET https://active-jobs-db.p.rapidapi.com/active-ats-7d
  ?limit=5&offset=0
  &advanced_title_filter='Data Engineer' | 'ML Engineer'
  &remote=true
  &include_ai=true
```

**Response (200 OK, 1.58s, 5 jobs):**

| # | Title | Company | Location | Platform | Salary | Skills |
|---|---|---|---|---|---|---|
| 1 | Senior Data Engineer | Centene Corporation | Georgia, US (Remote) | Workday | $87,000 - $161,300 | Data Pipelines, Data Ingestion, Data Transformation |
| 2 | Data Engineer II | Centene Corporation | Georgia, US (Remote) | Workday | $63,600 - $114,600 | Data Pipelines, Data Ingestion, Data Transformation |
| 3 | Senior Data Engineer | Apartment List | US (Remote) | Gem | $126,000 - $180,000 | Apache Airflow, BigQuery, DBT, Data Modeling |
| 4 | Staff Data Engineer | SmithRx | Remote | Greenhouse | — | PySpark, SQL, Python, C#, C++ |
| 5 | Senior Staff Data Engineer | SmithRx | Remote | Greenhouse | — | Data Modeling, Snowflake, PySpark, SQL |

---

## Test 5: Multi-title + Location Filter (LIVE)

```
POST /api/v1/job-search
```

**Request:**
```json
{
  "type": "LINKEDIN",
  "advanced_title_filter": ["Program Manager", "Product Manager", "Scrum Master"],
  "limit": 5,
  "location_filter": ["New York", "Boston"],
  "type_filter": "FULL_TIME",
  "include_ai": true
}
```

**Query sent to RapidAPI:**
```
GET https://linkedin-job-search-api.p.rapidapi.com/active-jb-7d
  ?limit=5&offset=0
  &advanced_title_filter='Program Manager' | 'Product Manager' | 'Scrum Master'
  &location_filter="New York" OR "Boston"
  &type_filter=FULL_TIME
  &include_ai=true
```

**Response (200 OK, 1.63s, 5 jobs):**

| # | Title | Company | Location | Company Size |
|---|---|---|---|---|
| 1 | AI Product Manager | Fortylaunch | New York, NY | 2 employees |
| 2 | Provisioning & Stored Cards Product Manager, VP | hackajob | New York, NY | 118 employees |
| 3 | Product Manager - Payments Platform, VP | hackajob | New York, NY | 118 employees |
| 4 | Lead Technical Program Manager | The Walt Disney Company | New York, NY | 187,180 employees |
| 5 | Vice President Product Manager - QuickDeposit | JPMorganChase | New York, NY | 225,325 employees |

---

## Test 6: Validation Errors

| Case | Request | Expected | Actual | Status |
|---|---|---|---|---|
| No `type` field | `{"advanced_title_filter": ["Engineer"]}` | 422 | 422 | PASS |
| No titles | `{"type": "LINKEDIN"}` | 422 | 422 | PASS |
| Empty titles | `{"type": "LINKEDIN", "advanced_title_filter": []}` | 422 | 422 | PASS |
| Invalid type | `{"type": "GOOGLE", "advanced_title_filter": ["PM"]}` | 422 | 422 | PASS |

---

## Cost Breakdown

### RapidAPI Calls Made

| Call | API | Endpoint | Jobs Returned | Est. Cost (Pro Plan) |
|---|---|---|---|---|
| Test 3 | LinkedIn | /active-jb-7d | 5 | $0.006 (5 x $1.25/1K) |
| Test 4 | ATS | /active-ats-7d | 5 | $0.013 (5 x $2.50/1K) |
| Test 5 | LinkedIn | /active-jb-7d | 5 | $0.006 (5 x $1.25/1K) |
| **Total** | | | **15 jobs** | **~$0.025** |

### LLM / Other API Calls

| Service | Calls | Tokens | Cost |
|---|---|---|---|
| Groq (Job Titles) | 0 (requires file upload — not tested here) | 0 | $0.00 |
| SerpAPI (Salary) | 0 (no SERPAPI_KEY configured) | 0 | $0.00 |
| HuggingFace (Salary) | 0 (depends on SerpAPI) | 0 | $0.00 |

### Total Cost: ~$0.025 (15 jobs fetched via RapidAPI)

---

## Performance

| Metric | Value |
|---|---|
| Total test time | 4.94s |
| Avg API response time | ~1.6s per call |
| Local endpoint time (no API) | <0.01s |
| DB operations | <0.01s (SQLite) |

---

## Services Not Tested (Live)

| Service | Reason | How to Test |
|---|---|---|
| Job Title (`/suggest-titles`) | Requires multipart form-data with resume file upload | Use Postman with a PDF resume |
| Salary Estimator (`/estimate-salary`) | No `SERPAPI_KEY` configured in .env | Add key and send POST with job data |
