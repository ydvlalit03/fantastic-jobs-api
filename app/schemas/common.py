from enum import Enum

from pydantic import BaseModel, Field


# ── Source selection ──────────────────────────────────────────────────────────

class SourceType(str, Enum):
    LINKEDIN = "linkedin"
    ATS = "ats"
    BOTH = "both"


# ── Description type ─────────────────────────────────────────────────────────

class DescriptionType(str, Enum):
    TEXT = "text"
    HTML = "html"
    NONE = ""


# ── Employment / Job type ────────────────────────────────────────────────────

class EmploymentType(str, Enum):
    FULL_TIME = "FULL_TIME"
    PART_TIME = "PART_TIME"
    CONTRACTOR = "CONTRACTOR"
    TEMPORARY = "TEMPORARY"
    INTERN = "INTERN"
    VOLUNTEER = "VOLUNTEER"
    PER_DIEM = "PER_DIEM"
    OTHER = "OTHER"


# LinkedIn-specific type_filter values (slightly different set)
class LinkedInJobType(str, Enum):
    CONTRACTOR = "CONTRACTOR"
    FULL_TIME = "FULL_TIME"
    INTERN = "INTERN"
    OTHER = "OTHER"
    PART_TIME = "PART_TIME"
    TEMPORARY = "TEMPORARY"
    VOLUNTEER = "VOLUNTEER"


# ── Work arrangement ─────────────────────────────────────────────────────────

class WorkArrangement(str, Enum):
    ON_SITE = "On-site"
    HYBRID = "Hybrid"
    REMOTE_OK = "Remote OK"
    REMOTE_SOLELY = "Remote Solely"


# ── Experience levels ────────────────────────────────────────────────────────

class ExperienceLevelATS(str, Enum):
    """ATS API uses 0-2 for entry level."""
    ENTRY = "0-2"
    MID = "2-5"
    SENIOR = "5-10"
    EXECUTIVE = "10+"


class ExperienceLevelLinkedIn(str, Enum):
    """LinkedIn API uses 0-3 for entry level."""
    ENTRY = "0-3"
    MID = "2-5"
    SENIOR = "5-10"
    EXECUTIVE = "10+"


# ── Seniority (LinkedIn only) ────────────────────────────────────────────────

class SeniorityLevel(str, Enum):
    ASSOCIATE = "Associate"
    DIRECTOR = "Director"
    EXECUTIVE = "Executive"
    MID_SENIOR = "Mid-Senior level"
    ENTRY = "Entry level"
    NOT_APPLICABLE = "Not Applicable"
    INTERNSHIP = "Internship"


# ── ATS Source platforms ─────────────────────────────────────────────────────

ATS_PLATFORMS = [
    "adp", "applicantpro", "ashby", "bamboohr", "breezy", "careerplug",
    "comeet", "csod", "dayforce", "dover", "eightfold", "firststage",
    "freshteam", "gem", "gohire", "greenhouse", "hibob", "hirebridge",
    "hirehive", "hireology", "hiringthing", "icims", "isolved", "jazzhr",
    "jobvite", "join.com", "kula", "lever.co", "manatal", "oraclecloud",
    "pageup", "paradox", "paycom", "paycor", "paylocity", "personio",
    "phenompeople", "pinpoint", "polymer", "recruitee", "recooty",
    "rippling", "rival", "smartrecruiters", "successfactors", "taleo",
    "teamtailor", "trakstar", "trinet", "ultipro", "werecruit", "workable",
    "workday", "zoho",
]


# ── AI Taxonomy categories ───────────────────────────────────────────────────

AI_TAXONOMY_CATEGORIES = [
    "Technology", "Healthcare", "Management & Leadership",
    "Finance & Accounting", "Human Resources", "Sales", "Marketing",
    "Customer Service & Support", "Education", "Legal", "Engineering",
    "Science & Research", "Trades", "Construction", "Manufacturing",
    "Logistics", "Creative & Media", "Hospitality",
    "Environmental & Sustainability", "Retail", "Data & Analytics",
    "Software", "Energy", "Agriculture", "Social Services",
    "Administrative", "Government & Public Sector", "Art & Design",
    "Food & Beverage", "Transportation", "Consulting",
    "Sports & Recreation", "Security & Safety",
]


# ── ATS Endpoint selection ───────────────────────────────────────────────────

class ATSEndpoint(str, Enum):
    ACTIVE_7D = "/active-ats-7d"
    ACTIVE_24H = "/active-ats-24h"
    HOURLY = "/active-ats-1h"
    EXPIRED = "/expired-ats"
    BACKFILL_6M = "/active-ats-6m"


# ── LinkedIn Endpoint selection ──────────────────────────────────────────────

class LinkedInEndpoint(str, Enum):
    ACTIVE_7D = "/active-jb-7d"
    ACTIVE_24H = "/active-jb-24h"
    BACKFILL_6M = "/active-jb-6m"
    HOURLY = "/ultra/active-jb-1h"
    EXPIRED = "/ultra/expired-jb"


# ── Pagination ───────────────────────────────────────────────────────────────

class PaginationParams(BaseModel):
    page: int = Field(1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(100, ge=10, le=100, description="Results per page (10-100)")

    @property
    def limit(self) -> int:
        return self.page_size

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


# ── Sort order (LinkedIn only) ───────────────────────────────────────────────

class SortOrder(str, Enum):
    DESC = "desc"
    ASC = "asc"
