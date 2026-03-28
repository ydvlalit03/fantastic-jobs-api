"""Build search queries for salary estimation."""

import re

TECH_COMPANIES = {
    "google", "microsoft", "amazon", "meta", "apple", "netflix", "uber", "oracle",
    "salesforce", "adobe", "intel", "cisco", "qualcomm", "nvidia", "twitter", "x",
    "paypal", "stripe", "linkedin", "spotify", "atlassian", "vmware", "sap", "ibm",
    "airbnb", "doordash", "snap", "pinterest", "databricks", "snowflake", "palantir",
    "coinbase", "robinhood", "dropbox", "slack", "zoom", "shopify", "block", "square",
    "lyft", "instacart", "roblox", "discord", "figma", "notion", "openai", "anthropic",
}

FINANCE_COMPANIES = {
    "goldman sachs", "morgan stanley", "jp morgan", "jpmorgan", "jpmorgan chase",
    "deutsche bank", "barclays", "bank of america", "citibank", "citi", "wells fargo",
    "blackrock", "citadel", "two sigma", "jane street", "de shaw", "bridgewater",
    "point72", "kkr", "blackstone", "apollo", "carlyle",
}

CONSULTING_COMPANIES = {
    "mckinsey", "bain", "bcg", "boston consulting", "deloitte", "pwc",
    "pricewaterhousecoopers", "ernst & young", "ey", "kpmg", "accenture", "capgemini",
    "booz allen", "oliver wyman",
}


def _normalize_experience(exp: str | None) -> str | None:
    if not exp:
        return None
    cleaned = exp.lower().strip()
    if cleaned in ("fresher", "fresh", "entry level", "entry-level"):
        return "0"
    match = re.search(r"(\d+)", cleaned)
    return match.group(1) if match else None


def _exp_to_seniority(exp_years: str) -> str:
    years = int(exp_years)
    if years == 0:
        return "entry level new grad"
    elif years <= 2:
        return "junior"
    elif years <= 5:
        return "mid level"
    elif years <= 10:
        return "senior"
    elif years <= 15:
        return "staff principal"
    else:
        return "director distinguished"


def _exp_to_level_hint(exp_years: str, company_lower: str) -> str | None:
    years = int(exp_years)
    if company_lower in ("google", "alphabet"):
        if years <= 2: return "L3"
        elif years <= 5: return "L4"
        elif years <= 8: return "L5"
        elif years <= 12: return "L6"
        else: return "L7"
    elif company_lower in ("meta", "facebook"):
        if years <= 2: return "E3"
        elif years <= 5: return "E4"
        elif years <= 8: return "E5"
        elif years <= 12: return "E6"
        else: return "E7"
    elif company_lower in ("amazon",):
        if years <= 2: return "SDE1"
        elif years <= 5: return "SDE2"
        elif years <= 10: return "SDE3"
        else: return "Principal"
    elif company_lower in ("apple",):
        if years <= 2: return "ICT2"
        elif years <= 5: return "ICT3"
        elif years <= 8: return "ICT4"
        elif years <= 12: return "ICT5"
        else: return "ICT6"
    elif company_lower in ("microsoft",):
        if years <= 2: return "L59 L60"
        elif years <= 5: return "L61 L62"
        elif years <= 8: return "L63 L64"
        elif years <= 12: return "L65 L66"
        else: return "L67"
    return None


def _get_site_hints(company_lower: str) -> list[str]:
    if company_lower in TECH_COMPANIES:
        return ["levels.fyi", "blind teamblind", "glassdoor"]
    elif company_lower in FINANCE_COMPANIES:
        return ["glassdoor", "wallstreetoasis", "salary.com"]
    elif company_lower in CONSULTING_COMPANIES:
        return ["glassdoor", "managementconsulted", "fishbowlapp"]
    else:
        return ["glassdoor", "payscale", "salary.com indeed"]


def get_experience_context(company_name: str, years_of_experience: str | None) -> dict:
    exp_years = _normalize_experience(years_of_experience)
    if exp_years is None:
        return {"exp_years": None, "seniority": None, "level_hint": None}
    company_lower = company_name.lower().strip()
    return {
        "exp_years": exp_years,
        "seniority": _exp_to_seniority(exp_years),
        "level_hint": _exp_to_level_hint(exp_years, company_lower),
    }


def build_queries(company_name: str, designation: str, years_of_experience: str | None, location: str) -> list[str]:
    company_lower = company_name.lower().strip()
    exp_years = _normalize_experience(years_of_experience)
    sites = _get_site_hints(company_lower)
    has_exp = exp_years is not None

    queries: list[str] = []

    q1 = f"{designation} salary at {company_name} {location} {sites[0]}"
    queries.append(q1)

    q2 = f"{company_name} {designation} total compensation 2025 2026 {sites[1]}"
    queries.append(q2)

    if has_exp:
        seniority = _exp_to_seniority(exp_years)
        q3a = f"{company_name} {designation} {exp_years} years experience salary {location}"
        queries.append(q3a)
        q3b = f"{seniority} {designation} salary at {company_name} {sites[0]}"
        queries.append(q3b)
        level_hint = _exp_to_level_hint(exp_years, company_lower)
        if level_hint:
            q3c = f"{company_name} {level_hint} {designation} compensation levels.fyi blind"
            queries.append(q3c)

    if has_exp:
        q4 = f"{designation} {exp_years} years experience salary {location} average 2025 {sites[2]}"
    else:
        q4 = f"{designation} average salary {location} 2025 {sites[2]}"
    queries.append(q4)

    seen: set[str] = set()
    unique: list[str] = []
    for q in queries:
        normalized = " ".join(q.lower().split())
        if normalized not in seen:
            seen.add(normalized)
            unique.append(q)

    return unique
