# Fantastic Jobs API

A unified, multi-tenant **FastAPI** backend that serves three job-market services behind a single versioned API: **job-search aggregation**, **resume-to-title generation**, and **salary estimation**. One backend, one set of conventions (config, auth, logging, error handling), three independently useful capabilities.

---

## Services

### Fantastic Jobs — Job Search & Aggregation
- Aggregates listings from **ATS** and **LinkedIn** sources
- Smart query builder + search orchestrator
- Normalizer unifies results into one schema
- Multi-tenant per-client configuration

### Job Title — Resume → Title
- Parses **PDF / DOCX resumes** (`PyPDF2`, `python-docx`)
- Generates accurate, market-relevant job titles via **Groq LLM**

### Salary Estimator
- Estimates market salary using live web search + LLM reasoning
- Confidence scoring based on data quality and agreement

---

## Tech Stack

- **Framework**: FastAPI + Uvicorn (async)
- **Validation**: Pydantic v2 + pydantic-settings
- **Database**: SQLAlchemy 2 (async) + asyncpg (PostgreSQL), Alembic
- **LLM**: Groq
- **Resilience**: httpx, tenacity (retries), cachetools
- **Ops**: trace-ID middleware, structured logging, security headers, CORS

---

## API Layout

All routes under `/api/v1`:

| Endpoint | Service |
|----------|---------|
| `/job_search` | Job search & aggregation |
| `/job_title` | Resume → job-title generation |
| `/salary` | Salary estimation |
| `/search` | Unified / cross search |
| `/clients` | Multi-tenant client config |

---

## Quick Start

### Prerequisites

- Python 3.11+, PostgreSQL, a **Groq API key**

### Setup

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env            # set DATABASE_URL, GROQ_API_KEY
alembic upgrade head

python run.py                   # or: uvicorn app.main:app --reload
```

API docs at `http://localhost:8000/docs`.

---

## Project Structure

```
app/
├── main.py            # FastAPI app, lifespan, middleware
├── api/v1/            # router + endpoints (job_search, job_title, salary, search, clients)
├── services/
│   ├── fantastic_jobs/   # ATS/LinkedIn clients, query builder, orchestrator, normalizer
│   ├── job_title/        # resume parser, context builder, LLM, title generator
│   └── salary_estimator/ # search, LLM, confidence services
├── schemas/           # request/response models
├── db/                # async engine, session, models
├── core/              # config, logging, exceptions
└── middleware/        # security headers, trace IDs
```
