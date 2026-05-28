"""Job title suggestion endpoint — POST /api/v1/suggest-titles."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.job_title import TitleResponse
from app.services.job_title.context_builder import build_context
from app.services.job_title.title_generator import generate_titles

logger = logging.getLogger("app.job_title")

router = APIRouter(tags=["job-title"])


@router.post("/suggest-titles", response_model=TitleResponse, summary="Suggest job titles from resume + profile")
async def suggest_titles(
    name: str = Form(...),
    id: str = Form(...),
    linkedinProfileUrl: str = Form(...),
    questionnaire: str = Form(...),
    linkedinProfile: Optional[str] = Form(None),
    additionalInfo: Optional[str] = Form(None),
    resume: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    logger.info("[API] POST /suggest-titles | client=%s (%s)", name, id)

    # Validate file type
    if not resume.filename.lower().endswith((".pdf", ".docx", ".doc")):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF and Word (.docx) files are accepted.")

    # Build context
    try:
        context_input = build_context(
            questionnaire_raw=questionnaire,
            linkedin_raw=linkedinProfile,
            additional_info=additionalInfo,
        )
    except Exception as e:
        logger.error("[API] Failed to build context: %s", e)
        raise HTTPException(status_code=400, detail=f"Failed to process input data: {e}")

    # Generate titles
    try:
        titles = await generate_titles(context=context_input, resume_file=resume)
    except ValueError as e:
        logger.error("[API] Title generation failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error("[API] Title generation failed: %s: %s", type(e).__name__, e)
        raise HTTPException(status_code=503, detail="AI service temporarily unavailable. Please try again.")

    response = TitleResponse(name=name, id=id, titles=titles)
    logger.info("[API] Returning %d titles for client %s", len(titles), id)
    return response
