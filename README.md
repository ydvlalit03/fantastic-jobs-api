# 🚀 Fantastic Jobs API

> A **unified, multi-tenant FastAPI backend** that serves three job-market services behind a single versioned API: **Job Search aggregation**, **Job Title generation**, and **Salary Estimation**.

One backend, one set of conventions (config, auth, logging, error handling), three independently useful capabilities — designed so client apps can consume job-market intelligence from a single integration point.

---

## ✨ Services

### 1. 🔎 Fantastic Jobs — Job Search & Aggregation
- Aggregates job listings from **ATS** and **LinkedIn** sources
- Smart **query builder** and **search orchestrator**
- **Normalizer** unifies results into one consistent schema
- Multi-tenant: per-client configuration (`ClientConfig`)

### 2. 🏷️ Job Title — Resume → Title
- Parses **PDF / DOCX resumes** (`PyPDF2`, `python-docx`)
- Builds context and generates accurate, market-relevant job titles
- Powered by **Groq LLM** for fast inference

### 3. 💰 Salary Estimator
- Estimates market salary using live web search + LLM reasoning
- **Confidence scoring** based on data quality and agreement
- Shared async HTTP client for efficient outbound calls

---

## 🛠️ Tech Stack

| Concern        | Tech                                                |
|----------------|-----------------------------------------------------|
| Framework      | FastAPI + Uvicorn (async)                           |
| Validation     | Pydantic v2 + pydantic-settings                     |
| Database       | SQLAlchemy 2 (async) + asyncpg (PostgreSQL)         |
| Migrations     | Alembic                                             |
| LLM            | Groq                                                |
| HTTP / Resilience | httpx, tenacity (retries), cachetools (caching)  |
| Observability  | Trace-ID middleware, structured logging             |
| Security       | Security-headers middleware, CORS                   |

---

## 🗂️ API Layout

All routes are served under a versioned router (`/api/v1`):

| Endpoint        | Service                       |
|-----------------|-------------------------------|
| `/job_search`   | Job search & aggregation      |
| `/job_title`    | Resume → job-title generation |
| `/salary`       | Salary estimation             |
| `/search`       | Unified/cross search          |
| `/clients`      | Multi-tenant client config    |

---

## 🏗️ Project Structure

```
app/
├── main.py                 # FastAPI app, lifespan, middleware
├── api/v1/
│   ├── router.py           # aggregates all endpoint routers
│   └── endpoints/          # job_search, job_title, salary, search, clients
├── services/
│   ├── fantastic_jobs/     # ats/linkedin clients, query builder, orchestrator, normalizer
│   ├── job_title/          # resume parser, context builder, LLM, title generator
│   └── salary_estimator/   # search, LLM, confidence services
├── schemas/                # request/response Pydantic models
├── db/                     # async engine, session, models
├── core/                   # config, logging, exceptions
├── middleware/             # security headers, trace IDs
└── prompts/                # LLM prompt templates
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- PostgreSQL
- A **Groq API key**

### Setup

```bash
# 1. Install dependencies
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
#    Set DATABASE_URL, GROQ_API_KEY and any job-source API keys

# 3. Run migrations
alembic upgrade head

# 4. Start the API
python run.py          # or: uvicorn app.main:app --reload
```

API docs available at `http://localhost:8000/docs` once running.

---

## 📄 License

For educational and demonstration purposes.
