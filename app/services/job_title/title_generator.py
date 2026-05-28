"""Main pipeline: resume + context → LLM → title suggestions."""

import logging

from fastapi import UploadFile

from app.prompts.title_prompt import SYSTEM_PROMPT, build_user_prompt
from app.schemas.job_title import ContextInput, TitleSuggestionItem
from app.services.job_title.llm_service import call_groq
from app.services.job_title.resume_parser import parse_resume

logger = logging.getLogger("app.job_title")


async def generate_titles(
    context: ContextInput,
    resume_file: UploadFile,
) -> list[TitleSuggestionItem]:
    logger.info("[TITLE GENERATOR] Starting pipeline")

    # Step 1: Parse resume
    resume_text = await parse_resume(resume_file)

    # Step 2: Build prompt
    user_prompt = build_user_prompt(
        resume_text=resume_text,
        goal=context.goal,
        linkedin_profile=context.linkedinProfile,
        questionnaire=context.questionnaire,
        additional_info=context.additionalInfo,
    )

    # Step 3: Call LLM
    raw_titles = call_groq(SYSTEM_PROMPT, user_prompt)

    # Step 4: Validate and convert
    titles = []
    for i, raw in enumerate(raw_titles):
        try:
            item = TitleSuggestionItem(
                title=raw["title"],
                description=raw["description"],
                score=raw["score"],
            )
            titles.append(item)
        except (KeyError, ValueError) as e:
            logger.warning("[TITLE GENERATOR] Skipping invalid title at index %d: %s", i, e)

    titles.sort(key=lambda x: x.score, reverse=True)
    logger.info("[TITLE GENERATOR] Pipeline complete - %d titles", len(titles))
    return titles
