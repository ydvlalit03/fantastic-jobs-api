"""Schemas for the Salary Estimator service."""

import re

from pydantic import BaseModel, Field, field_validator


class JobEntry(BaseModel):
    companyName: str = Field(min_length=1)
    designation: str = Field(min_length=1)
    yearsOfExperience: str | None = None
    location: str = Field(min_length=1)

    @field_validator("companyName", "designation", "location", mode="before")
    @classmethod
    def sanitize_string(cls, v: str) -> str:
        if not isinstance(v, str):
            return v
        return re.sub(r"<[^>]*>", "", v).strip()


class SalaryRequest(BaseModel):
    serpApiKey: str = Field(min_length=1)
    jobs: list[JobEntry] = Field(min_length=1)


class SalaryRange(BaseModel):
    lower: str | None = None
    upper: str | None = None


class SalaryResult(BaseModel):
    companyName: str
    designation: str
    yearsOfExperience: str | None = None
    location: str
    estimatedSalary: str | None = None
    salaryRange: SalaryRange | None = None
    confidenceScore: float = 0.0
    sources: list[str] = []
    error: str | None = None


class SalaryResponse(BaseModel):
    success: bool = True
    count: int = 0
    results: list[SalaryResult] = []
    trace_id: str | None = None
