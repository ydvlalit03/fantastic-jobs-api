from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Fantastic Jobs API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False
    LOG_ENABLED: bool = True
    LOG_LEVEL: str = "INFO"
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/fantastic_jobs"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10

    # RapidAPI (Fantastic Jobs)
    RAPIDAPI_KEY: str = ""
    ATS_API_HOST: str = "active-jobs-db.p.rapidapi.com"
    ATS_API_BASE_URL: str = "https://active-jobs-db.p.rapidapi.com"
    LINKEDIN_API_HOST: str = "linkedin-job-search-api.p.rapidapi.com"
    LINKEDIN_API_BASE_URL: str = "https://linkedin-job-search-api.p.rapidapi.com"

    # Job Title Service (Groq LLM)
    GROQ_API_KEY: str = ""
    ENABLE_TITLE_LOGS: bool = True

    # Salary Estimator Service
    SERPAPI_KEY: str = ""
    HF_API_TOKEN: str = ""
    HF_MODEL_ID: str = "mistralai/Mistral-7B-Instruct-v0.3"
    MAX_BATCH_SIZE: int = 10
    MAX_CONCURRENT_SEARCHES: int = 5
    ENABLE_TRACE_LOGS: bool = True

    # Rate limiting
    RAPIDAPI_MAX_CONCURRENT: int = 5
    HTTP_TIMEOUT: int = 30

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()
