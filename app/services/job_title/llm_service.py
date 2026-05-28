"""Groq LLM service for job title generation."""

import json
import logging

from groq import Groq

from app.core.config import get_settings

logger = logging.getLogger("app.job_title")

MODEL = "llama-3.3-70b-versatile"


def call_groq(system_prompt: str, user_prompt: str) -> list[dict]:
    settings = get_settings()
    client = Groq(api_key=settings.GROQ_API_KEY)

    logger.info("[LLM SERVICE] Calling Groq API - model: %s", MODEL)

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=4096,
        )

        raw_content = response.choices[0].message.content
        logger.info("[LLM SERVICE] Response received - %d chars", len(raw_content))
        logger.info(
            "[LLM SERVICE] Token usage - prompt: %d, completion: %d, total: %d",
            response.usage.prompt_tokens,
            response.usage.completion_tokens,
            response.usage.total_tokens,
        )

        cleaned = raw_content.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
            cleaned = cleaned.rsplit("```", 1)[0]

        titles = json.loads(cleaned)
        logger.info("[LLM SERVICE] Parsed %d titles from response", len(titles))
        return titles

    except json.JSONDecodeError as e:
        logger.error("[LLM SERVICE] Failed to parse LLM response as JSON: %s", e)
        raise ValueError(f"LLM returned invalid JSON: {e}")

    except Exception as e:
        logger.error("[LLM SERVICE] Groq API call failed: %s: %s", type(e).__name__, e)
        raise
