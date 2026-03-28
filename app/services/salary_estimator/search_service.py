"""Search salary data via SerpAPI."""

import logging
from urllib.parse import urlparse

import httpx

from app.utils.query_builder import build_queries, get_experience_context
from app.utils.rate_limiter import serpapi_limiter

logger = logging.getLogger("app.salary_estimator")

SERPAPI_URL = "https://serpapi.com/search.json"

TRUSTED_DOMAINS = [
    "glassdoor.com", "levels.fyi", "payscale.com", "indeed.com",
    "linkedin.com", "salary.com", "comparably.com", "teamblind.com",
    "builtin.com", "ziprecruiter.com", "dice.com", "hired.com",
    "h1bdata.info", "blind",
]

RELEVANCE_KEYWORDS = {"salary", "compensation", "pay", "$", "total comp", "base", "tc", "offer"}

SENIORITY_TIERS = {
    "entry": {"entry level", "entry-level", "new grad", "junior", "associate", "l3", "e3", "sde1", "sde 1", "ict2", "l59", "l60", "0-2 year", "1-3 year"},
    "mid": {"mid level", "mid-level", "l4", "e4", "sde2", "sde 2", "ict3", "l61", "l62", "3-5 year", "2-5 year"},
    "senior": {"senior", "sr.", "l5", "e5", "sde3", "sde 3", "ict4", "l63", "l64", "5-10 year", "5+ year"},
    "staff": {"staff", "principal", "l6", "l7", "e6", "e7", "ict5", "ict6", "l65", "l66", "l67", "10+ year", "10-15 year"},
    "director": {"director", "distinguished", "vp", "vice president", "l8", "l9", "l10", "15+ year", "20+ year"},
}


def _relevant_tiers_for_exp(exp_years: str | None) -> set[str]:
    if exp_years is None:
        return {"entry", "mid", "senior", "staff", "director"}
    years = int(exp_years)
    if years <= 2:
        return {"entry", "mid"}
    elif years <= 5:
        return {"mid", "entry", "senior"}
    elif years <= 10:
        return {"senior", "mid", "staff"}
    elif years <= 15:
        return {"staff", "senior", "director"}
    else:
        return {"director", "staff"}


def _detect_snippet_tier(text: str) -> str | None:
    text_lower = text.lower()
    matches: dict[str, int] = {}
    for tier, keywords in SENIORITY_TIERS.items():
        count = sum(1 for kw in keywords if kw in text_lower)
        if count > 0:
            matches[tier] = count
    if not matches:
        return None
    return max(matches, key=matches.get)


def _extract_domain(url: str) -> str:
    try:
        return urlparse(url).hostname.replace("www.", "")
    except Exception:
        return ""


def _is_relevant(result: dict) -> bool:
    combined = f"{result.get('title', '')} {result.get('snippet', '')}".lower()
    return any(kw in combined for kw in RELEVANCE_KEYWORDS)


def _is_trusted(domain: str) -> bool:
    return any(td in domain for td in TRUSTED_DOMAINS)


async def search_salary_data(
    client: httpx.AsyncClient,
    company_name: str,
    designation: str,
    years_of_experience: str | None,
    location: str,
    serp_api_key: str = "",
) -> list[dict]:
    queries = build_queries(company_name, designation, years_of_experience, location)
    exp_ctx = get_experience_context(company_name, years_of_experience)
    relevant_tiers = _relevant_tiers_for_exp(exp_ctx["exp_years"])

    all_results: list[dict] = []

    for query in queries:
        try:
            await serpapi_limiter.acquire()
            params = {
                "engine": "google",
                "q": query,
                "location": f"{location}, United States" if location else "United States",
                "gl": "us",
                "hl": "en",
                "num": 5,
                "api_key": serp_api_key,
            }
            response = await client.get(SERPAPI_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            for r in data.get("organic_results", []):
                if _is_relevant(r):
                    domain = _extract_domain(r.get("link", ""))
                    combined_text = f"{r.get('title', '')} {r.get('snippet', '')}"
                    snippet_tier = _detect_snippet_tier(combined_text)

                    if snippet_tier is None:
                        exp_relevance = 0.5
                    elif snippet_tier in relevant_tiers:
                        exp_relevance = 1.0
                    else:
                        exp_relevance = 0.1

                    all_results.append({
                        "title": r.get("title", ""),
                        "snippet": r.get("snippet", ""),
                        "link": r.get("link", ""),
                        "domain": domain,
                        "is_trusted": _is_trusted(domain),
                        "snippet_tier": snippet_tier,
                        "exp_relevance": exp_relevance,
                    })
        except Exception as e:
            logger.warning("SERPAPI search failed for query='%s': %s", query, str(e))

    seen: set[str] = set()
    unique: list[dict] = []
    for r in all_results:
        if r["link"] not in seen:
            seen.add(r["link"])
            unique.append(r)

    unique.sort(key=lambda x: (x["exp_relevance"], x["is_trusted"]), reverse=True)
    return unique[:15]
