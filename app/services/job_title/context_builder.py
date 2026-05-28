"""Build context from raw questionnaire, LinkedIn, and additional info."""

import json
import logging
import re

from app.schemas.job_title import ContextInput

logger = logging.getLogger("app.job_title")


def clean_text(text: str) -> str:
    """Remove control characters, extra whitespace, and unicode artifacts."""
    text = re.sub(r'[\x00-\x09\x0b-\x0c\x0e-\x1f\x7f]', '', text)
    replacements = {
        '\u2019': "'", '\u2018': "'", '\u201c': '"', '\u201d': '"',
        '\u2013': '-', '\u2014': '-', '\u2026': '...', '\u00a0': ' ',
        '\u2022': '-', '\u25cf': '-', '\u27a8': '-', '\u2192': '-',
        '\ud835': '', '\u0308': '',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r'[^\x20-\x7E\n]', '', text)
    text = re.sub(r' {2,}', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def parse_linkedin_json(raw_json: str) -> str:
    """Extract relevant info from LinkedIn scraper JSON into a clean text summary."""
    try:
        data = json.loads(raw_json)
    except (json.JSONDecodeError, TypeError):
        logger.warning("[CONTEXT BUILDER] Failed to parse LinkedIn JSON, using as plain text")
        return clean_text(raw_json)

    if "data" in data and isinstance(data["data"], dict):
        data = data["data"]

    parts = []
    basic = data.get("basic_info", data)
    if basic.get("fullname"):
        parts.append(f"Name: {basic['fullname']}")
    if basic.get("headline"):
        parts.append(f"Headline: {basic['headline']}")
    if basic.get("about"):
        parts.append(f"About: {basic['about'][:500]}")
    if basic.get("top_skills"):
        parts.append(f"Top Skills: {', '.join(basic['top_skills'])}")
    location = basic.get("location", {})
    if isinstance(location, dict) and location.get("full"):
        parts.append(f"Location: {location['full']}")

    experience = data.get("experience", [])
    if experience:
        exp_lines = ["Experience:"]
        for exp in experience[:5]:
            title = exp.get("title", "")
            company = exp.get("company", "")
            duration = exp.get("duration", "")
            desc = exp.get("description", "")
            exp_lines.append(f"- {title} at {company} ({duration})")
            if desc:
                exp_lines.append(f"  {desc[:200].strip()}")
        parts.append("\n".join(exp_lines))

    education = data.get("education", [])
    if education:
        edu_lines = ["Education:"]
        for edu in education:
            school = edu.get("school", "")
            degree = edu.get("degree", edu.get("degree_name", ""))
            field = edu.get("field_of_study", "")
            line = f"- {degree}"
            if field:
                line += f", {field}"
            line += f" from {school}"
            edu_lines.append(line)
        parts.append("\n".join(edu_lines))

    certs = data.get("certifications", [])
    if certs:
        cert_lines = ["Certifications:"]
        for cert in certs:
            cert_lines.append(f"- {cert.get('name', '')} ({cert.get('issuer', '')})")
        parts.append("\n".join(cert_lines))

    result = "\n\n".join(parts)
    return clean_text(result)


def parse_questionnaire(raw_text: str) -> dict:
    """Parse raw questionnaire text and extract goal + structured info."""
    cleaned = clean_text(raw_text)
    goal = ""
    details = []
    lines = cleaned.split("\n")
    current_question = ""
    current_answer = []

    for line in lines:
        line = line.strip()
        if not line:
            if current_question and current_answer:
                answer_text = " ".join(current_answer).strip()
                if "job titles" in current_question.lower() and "targeting" in current_question.lower():
                    goal = answer_text
                else:
                    details.append(f"{current_question}: {answer_text}")
                current_question = ""
                current_answer = []
            continue

        if line.endswith("?"):
            if current_question and current_answer:
                answer_text = " ".join(current_answer).strip()
                if "job titles" in current_question.lower() and "targeting" in current_question.lower():
                    goal = answer_text
                else:
                    details.append(f"{current_question}: {answer_text}")
            current_question = line
            current_answer = []
        else:
            if current_question:
                current_answer.append(line)
            else:
                details.append(line)

    if current_question and current_answer:
        answer_text = " ".join(current_answer).strip()
        if "job titles" in current_question.lower() and "targeting" in current_question.lower():
            goal = answer_text
        else:
            details.append(f"{current_question}: {answer_text}")

    if not goal:
        goal = "Looking for relevant job opportunities matching my background"

    return {"goal": goal, "questionnaire_summary": "\n".join(details)}


def build_context(
    questionnaire_raw: str | None = None,
    linkedin_raw: str | None = None,
    additional_info: str | None = None,
) -> ContextInput:
    """Build a clean ContextInput from raw questionnaire and LinkedIn data."""
    logger.info("[CONTEXT BUILDER] Building context from raw inputs...")

    goal = "Looking for relevant job opportunities matching my background"
    questionnaire_summary = None
    linkedin_summary = None

    if questionnaire_raw:
        parsed_q = parse_questionnaire(questionnaire_raw)
        goal = parsed_q["goal"]
        questionnaire_summary = parsed_q["questionnaire_summary"]

    if linkedin_raw:
        linkedin_summary = parse_linkedin_json(linkedin_raw)

    cleaned_additional = clean_text(additional_info) if additional_info else None

    return ContextInput(
        goal=goal,
        linkedinProfile=linkedin_summary,
        questionnaire=questionnaire_summary,
        additionalInfo=cleaned_additional,
    )
