"""Regex-based salary extraction and estimation from text."""

import math
import re

# "$120,000 - $180,000" or "$120k - $180k"
RANGE_USD = re.compile(
    r"\$\s*(\d[\d,]*\.?\d*)\s*([kK])?\s*(?:to|-|–|—)\s*\$?\s*(\d[\d,]*\.?\d*)\s*([kK])?",
    re.IGNORECASE,
)

# "$150,000" or "$150k" or "$150K/yr"
SINGLE_USD = re.compile(
    r"\$\s*(\d[\d,]*\.?\d*)\s*([kK])?\s*(?:/?\s*(?:yr|year|annum|annually|per\s*year))?",
    re.IGNORECASE,
)

# "150,000 USD" or "150k USD"
USD_SUFFIX = re.compile(
    r"(\d[\d,]*\.?\d*)\s*([kK])?\s*(?:USD|usd)",
    re.IGNORECASE,
)

# "base salary of 150,000" or "total compensation 250,000"
COMP_PATTERN = re.compile(
    r"(?:base\s*salary|total\s*comp(?:ensation)?|salary|TC|OTE)\s*(?:of|is|:|\s)\s*\$?\s*(\d[\d,]*\.?\d*)\s*([kK])?",
    re.IGNORECASE,
)

MIN_SALARY = 10_000
MAX_SALARY = 1_000_000


def _parse_usd_value(num_str: str, suffix: str | None) -> float:
    val = float(num_str.replace(",", ""))
    if suffix and suffix.lower() == "k":
        val *= 1000
    return val


def extract_salaries(text: str) -> list[int]:
    salaries: list[float] = []

    for match in RANGE_USD.finditer(text):
        v1 = _parse_usd_value(match.group(1), match.group(2))
        v2 = _parse_usd_value(match.group(3), match.group(4))
        if MIN_SALARY < v1 < MAX_SALARY:
            salaries.append(v1)
        if MIN_SALARY < v2 < MAX_SALARY:
            salaries.append(v2)

    for match in SINGLE_USD.finditer(text):
        val = _parse_usd_value(match.group(1), match.group(2))
        if MIN_SALARY < val < MAX_SALARY:
            salaries.append(val)

    for match in USD_SUFFIX.finditer(text):
        val = _parse_usd_value(match.group(1), match.group(2))
        if MIN_SALARY < val < MAX_SALARY:
            salaries.append(val)

    for match in COMP_PATTERN.finditer(text):
        val = _parse_usd_value(match.group(1), match.group(2))
        if MIN_SALARY < val < MAX_SALARY:
            salaries.append(val)

    unique = sorted(set(round(s) for s in salaries))
    return unique


def _remove_outliers(values: list[int]) -> list[int]:
    if len(values) < 4:
        return values
    sorted_v = sorted(values)
    n = len(sorted_v)
    q1 = sorted_v[n // 4]
    q3 = sorted_v[(3 * n) // 4]
    iqr = q3 - q1
    if iqr == 0:
        return values
    lower_fence = q1 - 1.5 * iqr
    upper_fence = q3 + 1.5 * iqr
    filtered = [v for v in sorted_v if lower_fence <= v <= upper_fence]
    return filtered if filtered else values


def compute_estimate_from_values(values: list[int]) -> dict | None:
    if not values:
        return None
    cleaned = _remove_outliers(values)
    sorted_vals = sorted(cleaned)
    n = len(sorted_vals)

    if n % 2 == 0:
        median = (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2
    else:
        median = sorted_vals[n // 2]

    if n == 1:
        return {
            "estimated": round(median),
            "lower": round(median * 0.85),
            "upper": round(median * 1.15),
        }

    q1_idx = max(0, math.floor(n * 0.25))
    q3_idx = min(n - 1, math.ceil(n * 0.75))
    lower = sorted_vals[q1_idx]
    upper = sorted_vals[q3_idx]

    if lower == upper:
        lower = round(median * 0.85)
        upper = round(median * 1.15)

    return {
        "estimated": round(median),
        "lower": round(lower),
        "upper": round(upper),
    }
