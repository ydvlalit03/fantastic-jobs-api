<div align="center">

# 🚀 Fantastic Jobs API

### A unified, multi-tenant FastAPI backend serving three job-market services behind one API

![FastAPI](https://img.shields.io/badge/FastAPI-async-009688?style=flat-square&logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-asyncpg-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-LLM-F55036?style=flat-square&logo=groq&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063?style=flat-square&logo=pydantic&logoColor=white)

</div>

---

## 📖 Overview

**Fantastic Jobs API** consolidates three independently useful job-market capabilities into a single, production-shaped FastAPI service:

1. **Job Search & Aggregation** — pull and normalize listings from multiple sources
2. **Job Title Generation** — turn a resume into accurate, market-relevant job titles
3. **Salary Estimation** — estimate compensation with web evidence + LLM reasoning

Rather than running three separate microservices with three different conventions, everything shares **one backend**: a single config system, async database layer, logging, error handling, security middleware, and a versioned API surface. Client apps integrate once and get all three.

---

## 📑 Table of Contents

- [The three services](#-the-three-services)
- [Why one unified backend](#-why-one-unified-backend)
- [Architecture](#-architecture)
- [API reference](#-api-reference)
- [Tech stack](#-tech-stack)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Project structure](#-project-structure)
- [Operational features](#-operational-features)

---

## 🧩 The three services

### 1. 🔎 Fantastic Jobs — Job Search & Aggregation
- Aggregates job listings from **ATS** and **LinkedIn** clients
- A **query builder** turns user filters into provider-specific searches
- A **search orchestrator** fans out to sources and merges results
- A **normalizer** maps every provider's payload into one consistent schema
- **Multi-tenant**: per-client configuration (`ClientConfig`) so each consumer gets tailored behavior

### 2. 🏷️ Job Title — Resume → Title
- Parses **PDF and DOCX resumes** (`PyPDF2`, `python-docx`)
- A **context builder** assembles the relevant resume signal
- A **title generator** backed by **Groq LLM** produces accurate, market-aligned titles
- Prompt templates are versioned in `app/prompts/`

### 3. 💰 Salary Estimator
- Estimates market salary using live **web search** + **LLM reasoning**
- A **confidence service** scores the estimate based on data quality and agreement
- Uses a shared async HTTP client for efficient outbound calls

---

## 🎯 Why one unified backend

| Benefit | How |
|---------|-----|
| **Consistent conventions** | one config, logging, exception and middleware stack across all services |
| **Single integration** | clients hit one base URL and one auth model for three capabilities |
| **Shared infra** | one async DB engine, one HTTP client pool, one set of migrations |
| **Independent evolution** | each service lives in its own `services/` package and can change without touching the others |

---

## 🏗️ Architecture

```
                         ┌──────────────────────────────────────────┐
   client request ──────▶│              FastAPI (async)              │
                         │   middleware: TraceID, SecurityHeaders    │
                         │                    │                       │
                         │            /api/v1 router                  │
                         │      ┌─────────────┼─────────────┐         │
                         │      ▼             ▼             ▼         │
                         │  job_search    job_title      salary       │
                         │      │             │             │         │
                         │  fantastic_jobs/  job_title/  salary_       │
                         │  (ats, linkedin,  (parser,    estimator/    │
                         │   orchestrator,    context,   (search, llm, │
                         │   normalizer)      Groq)       confidence)   │
                         │      │                                       │
                         │  async SQLAlchemy ─▶ PostgreSQL (asyncpg)   │
                         └──────────────────────────────────────────┘
```

On startup the app creates DB tables and provisions a shared `httpx.AsyncClient`; on shutdown it cleans up gracefully via the FastAPI lifespan context.

---

## 🌐 API reference

All routes are served under a versioned router (`/api/v1`):

| Endpoint | Method | Service | Description |
|----------|--------|---------|-------------|
| `/job_search` | POST | Fantastic Jobs | search & aggregate listings across sources |
| `/job_title` | POST | Job Title | upload a resume → generated job titles |
| `/salary` | POST | Salary Estimator | estimate market salary with confidence |
| `/search` | POST | Unified | cross-service / combined search |
| `/clients` | — | Multi-tenant | manage per-client configuration |

Interactive docs at `http://localhost:8000/docs` (Swagger) and `/redoc`.

---

## 🛠️ Tech stack

| Concern | Technology |
|---------|------------|
| **Framework** | FastAPI + Uvicorn (fully async) |
| **Validation / settings** | Pydantic v2, pydantic-settings |
| **Database** | SQLAlchemy 2 (async) + asyncpg (PostgreSQL) |
| **Migrations** | Alembic |
| **LLM** | Groq |
| **HTTP / resilience** | httpx, tenacity (retries), cachetools (caching) |
| **Resume parsing** | PyPDF2, python-docx, python-multipart |
| **Observability** | Trace-ID middleware, structured logging |
| **Security** | security-headers middleware, CORS |

---

## 📦 Installation

### Prerequisites
- Python 3.11+
- PostgreSQL
- A **Groq API key**

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env            # set DATABASE_URL, GROQ_API_KEY, source keys
alembic upgrade head            # run migrations

python run.py                   # or: uvicorn app.main:app --reload
```

---

## ⚙️ Configuration

Key environment variables (see `.env.example`):

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | async PostgreSQL DSN (`postgresql+asyncpg://…`) |
| `GROQ_API_KEY` | Groq LLM access for title generation + salary reasoning |
| job-source keys | ATS / LinkedIn / search provider credentials |

---

## 🗂️ Project structure

```
app/
├── main.py                 # FastAPI app, lifespan, middleware wiring
├── api/v1/
│   ├── router.py           # aggregates all endpoint routers
│   └── endpoints/          # job_search, job_title, salary, search, clients
├── services/
│   ├── fantastic_jobs/     # ats_client, linkedin_client, query_builder,
│   │                       #   search_orchestrator, normalizer
│   ├── job_title/          # resume_parser, context_builder, llm_service, title_generator
│   └── salary_estimator/   # search_service, llm_service, confidence_service
├── schemas/                # request/response + filter Pydantic models
├── db/                     # async base, engine, session, models
├── core/                   # config, logging_config, exceptions
├── middleware/             # security headers, trace IDs
└── prompts/                # versioned LLM prompt templates
```

---

## 🔧 Operational features

- **Async everywhere** — async SQLAlchemy + a pooled `httpx.AsyncClient` (max 20 connections, 30s timeout) for high concurrency
- **Retries** — `tenacity` wraps flaky outbound calls
- **Caching** — `cachetools` to avoid redundant provider hits
- **Tracing** — every request carries a trace ID through structured logs
- **Hardened** — security-headers middleware + CORS configuration
