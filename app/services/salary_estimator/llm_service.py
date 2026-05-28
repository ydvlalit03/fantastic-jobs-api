"""HuggingFace LLM service for salary extraction."""

import json
import logging
import re

import httpx

from app.core.config import get_settings
from app.utils.logger import logger
from app.utils.query_builder import get_experience_context
from app.utils.rate_limiter import hf_limiter
from app.utils.salary_parser import compute_estimate_from_values, extract_salaries

HF_INFERENCE_URL = "https://router.huggingface.co/v1/chat/completions"


def _build_prompt(company_name: str, designation: str, years_of_experience: str | None, location: str, search_results: list[dict]) -> str:
    exp_ctx = get_experience_context(company_name, years_of_experience)

    snippet_parts = []
    for r in search_results:
        tier_tag = f" [TIER: {r.get('snippet_tier', 'unknown')}]" if r.get("snippet_tier") else ""
        snippet_parts.append(f"[{r['domain']}]{tier_tag} {r['title']}\n{r['snippet']}")
    snippets = "\n---\n".join(snippet_parts)[:3000]

    exp_instruction = ""
    if exp_ctx["exp_years"] is not None:
        exp_instruction = f"""
CRITICAL EXPERIENCE FILTER:
- The candidate has {exp_ctx['exp_years']} years of experience, which corresponds to "{exp_ctx['seniority']}" seniority level.
{f'- At {company_name}, this typically maps to level: {exp_ctx["level_hint"]}' if exp_ctx["level_hint"] else ''}
- ONLY extract salary data that matches this experience level. IGNORE salary figures for other levels.
- If snippets show a range like "$193K for L5 to $1.28M for L10", pick ONLY the value for the matching level ({exp_ctx.get("level_hint") or exp_ctx["seniority"]}).
- The upper and lower bounds should reflect the range for THIS specific level, NOT the entire company range across all levels.
"""
    else:
        exp_instruction = "\nNOTE: No specific experience level was provided. Extract the median/average salary data from the snippets.\n"

    return f"""You are a salary data extraction expert for the US job market. Given search result snippets about a job role, extract and estimate the annual salary in USD.

Job Details:
- Company: {company_name}
- Role: {designation}
- Experience: {years_of_experience or 'Not specified'}
- Location: {location}
{exp_instruction}
Search Results:
---
{snippets}
---

Based on the above search results, provide a JSON response with these exact fields:
{{
  "estimatedSalaryUSD": <number or null, annual salary in USD e.g. 150000>,
  "lowerBoundUSD": <number or null>,
  "upperBoundUSD": <number or null>,
  "dataPointsFound": <number>,
  "sourcesWithData": ["domain1", "domain2"]
}}

Rules:
1. All salary figures MUST be annual USD amounts. Convert hourly to annual (x2080). Convert "$150k" to 150000.
2. Focus on TOTAL COMPENSATION (base + bonus + stock) when available. If only base salary found, use that.
3. The lowerBoundUSD and upperBoundUSD MUST be for the SAME experience/seniority level. Do NOT use the company-wide min and max across all levels.
4. If search results show a range for the specific level, use it. If single figures, create a +/- 15% range.
5. If NO salary data matching the experience level is found in the snippets, return all values as null.
6. Return ONLY valid JSON, nothing else."""


def _parse_json_from_response(text: str) -> dict | None:
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return None
    try:
        parsed = json.loads(match.group(0))
        if isinstance(parsed.get("estimatedSalaryUSD"), (int, float)) or parsed.get("estimatedSalaryUSD") is None:
            return parsed
        return None
    except (json.JSONDecodeError, ValueError):
        return None


def _sanity_check_llm_output(parsed: dict) -> bool:
    estimated = parsed.get("estimatedSalaryUSD")
    lower = parsed.get("lowerBoundUSD")
    upper = parsed.get("upperBoundUSD")

    if estimated is None:
        return True

    if not (20_000 <= estimated <= 800_000):
        logger.warning("LLM SANITY FAIL: estimated=$%s out of range", estimated)
        return False

    if lower and upper and lower > 0:
        ratio = upper / lower
        if ratio > 3.0:
            logger.warning("LLM SANITY FAIL: range ratio %.1fx too wide", ratio)
            return False

    if lower and upper:
        if estimated < lower * 0.7 or estimated > upper * 1.3:
            logger.warning("LLM SANITY FAIL: estimated=$%s outside range", estimated)
            return False

    return True


async def extract_salary_with_llm(
    client: httpx.AsyncClient,
    company_name: str,
    designation: str,
    years_of_experience: str | None,
    location: str,
    search_results: list[dict],
) -> dict:
    settings = get_settings()
    all_snippet_text = " ".join(f"{r['title']} {r['snippet']}" for r in search_results)

    try:
        await hf_limiter.acquire()

        prompt = _build_prompt(company_name, designation, years_of_experience, location, search_results)

        payload = {
            "model": settings.HF_MODEL_ID,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 300,
            "temperature": 0.1,
        }

        headers = {
            "Authorization": f"Bearer {settings.HF_API_TOKEN}",
            "Content-Type": "application/json",
        }

        response = await client.post(HF_INFERENCE_URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        generated = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        parsed = _parse_json_from_response(generated)

        if parsed and parsed.get("estimatedSalaryUSD") is not None:
            if _sanity_check_llm_output(parsed):
                return {
                    "estimated": parsed["estimatedSalaryUSD"],
                    "lower": parsed.get("lowerBoundUSD"),
                    "upper": parsed.get("upperBoundUSD"),
                    "data_points": parsed.get("dataPointsFound", 0),
                    "sources": parsed.get("sourcesWithData", []),
                    "method": "llm",
                }

    except Exception as e:
        logger.warning("LLM extraction failed, falling back to regex: %s", str(e))

    # Fallback: regex extraction
    salary_values = extract_salaries(all_snippet_text)
    if not salary_values:
        return {"estimated": None, "lower": None, "upper": None, "data_points": 0, "sources": [], "method": "none"}

    estimate = compute_estimate_from_values(salary_values)
    source_domains = list({r["domain"] for r in search_results if r["is_trusted"]})

    return {
        "estimated": estimate["estimated"],
        "lower": estimate["lower"],
        "upper": estimate["upper"],
        "data_points": len(salary_values),
        "sources": source_domains,
        "method": "regex",
    }
