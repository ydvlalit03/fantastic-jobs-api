"""Confidence scoring for salary estimates."""

import logging
import math

logger = logging.getLogger("app.salary_estimator")

KNOWN_TECH = {
    "google", "microsoft", "amazon", "meta", "apple", "netflix", "uber", "oracle",
    "salesforce", "adobe", "intel", "cisco", "nvidia", "qualcomm", "twitter", "x",
    "paypal", "stripe", "linkedin", "spotify", "atlassian", "vmware", "sap", "ibm",
    "airbnb", "doordash", "snap", "pinterest", "databricks", "snowflake", "palantir",
    "coinbase", "robinhood", "dropbox", "zoom", "shopify", "block", "square",
    "lyft", "instacart", "roblox", "discord", "figma", "notion", "openai", "anthropic",
}

KNOWN_FINANCE = {
    "goldman sachs", "morgan stanley", "jp morgan", "jpmorgan", "jpmorgan chase",
    "deutsche bank", "barclays", "bank of america", "citibank", "citi", "wells fargo",
    "blackrock", "citadel", "two sigma", "jane street", "de shaw", "bridgewater",
}

KNOWN_COMPANIES = KNOWN_TECH | KNOWN_FINANCE | {
    "mckinsey", "bain", "bcg", "deloitte", "pwc", "ey", "kpmg", "accenture",
    "walmart", "target", "costco", "johnson & johnson", "pfizer", "unitedhealth",
    "boeing", "lockheed martin", "raytheon", "general motors", "ford", "tesla",
}

MAJOR_METROS = {
    "san francisco", "sf", "new york", "nyc", "new york city", "manhattan",
    "seattle", "los angeles", "la", "chicago", "boston", "austin", "denver",
    "washington dc", "dc", "san jose", "palo alto", "mountain view", "sunnyvale",
    "menlo park", "cupertino", "redmond", "bellevue",
    "san diego", "atlanta", "dallas", "houston", "philadelphia", "miami",
    "portland", "minneapolis", "raleigh", "charlotte", "nashville",
}

SECONDARY_CITIES = {
    "phoenix", "sacramento", "salt lake city", "tampa", "orlando", "columbus",
    "indianapolis", "pittsburgh", "st louis", "kansas city", "cincinnati",
    "richmond", "jacksonville", "milwaukee", "las vegas", "tucson", "omaha",
    "boise", "des moines", "madison", "ann arbor", "boulder",
}


def calculate_confidence(
    sources_count: int,
    salary_values: list[int | float],
    company_name: str,
    location: str,
    has_experience: bool,
    search_results: list[dict] | None = None,
) -> float:
    if sources_count == 0:
        source_score = 0.0
    elif sources_count == 1:
        source_score = 0.5
    elif sources_count == 2:
        source_score = 0.75
    else:
        source_score = 1.0

    consistency_score = 0.5
    if len(salary_values) > 1:
        mean = sum(salary_values) / len(salary_values)
        std = math.sqrt(sum((v - mean) ** 2 for v in salary_values) / len(salary_values))
        cv = std / mean
        if cv < 0.15:
            consistency_score = 1.0
        elif cv < 0.30:
            consistency_score = 0.7
        elif cv < 0.50:
            consistency_score = 0.4
        else:
            consistency_score = 0.1

    company_lower = company_name.lower().strip()
    company_score = 1.0 if company_lower in KNOWN_COMPANIES else 0.1

    location_lower = location.lower().strip()
    if location_lower in MAJOR_METROS:
        location_score = 1.0
    elif location_lower in SECONDARY_CITIES:
        location_score = 0.7
    else:
        location_score = 0.4

    experience_score = 1.0 if has_experience else 0.5

    mention_score = 0.0
    if search_results and len(search_results) > 0:
        company_terms = company_lower.split()
        mentioned = sum(
            1 for r in search_results
            if any(term in f"{r.get('title', '')} {r.get('snippet', '')}".lower() for term in company_terms)
        )
        mention_ratio = mentioned / len(search_results)
        if mention_ratio >= 0.5:
            mention_score = 1.0
        elif mention_ratio >= 0.3:
            mention_score = 0.7
        elif mention_ratio >= 0.1:
            mention_score = 0.4
        else:
            mention_score = 0.1

    weighted = (
        source_score * 0.25
        + consistency_score * 0.20
        + company_score * 0.15
        + location_score * 0.10
        + experience_score * 0.10
        + mention_score * 0.20
    )

    return round(weighted, 2)
