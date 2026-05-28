"""Parse resume files (PDF/DOCX) and extract text."""

import io
import logging

from fastapi import UploadFile
from PyPDF2 import PdfReader
from docx import Document

logger = logging.getLogger("app.job_title")


async def parse_resume(file: UploadFile) -> str:
    logger.info("[RESUME PARSER] Parsing %s (%s)", file.filename, file.content_type)

    content = await file.read()
    filename = file.filename.lower()

    if filename.endswith(".pdf"):
        text = _parse_pdf(content)
    elif filename.endswith(".docx") or filename.endswith(".doc"):
        text = _parse_docx(content)
    else:
        raise ValueError(f"Unsupported file type: {filename}. Only PDF and Word (.docx) files are accepted.")

    logger.info("[RESUME PARSER] Extracted %d characters", len(text))
    return text


def _parse_pdf(content: bytes) -> str:
    reader = PdfReader(io.BytesIO(content))
    text_parts = []
    for page in reader.pages:
        text_parts.append(page.extract_text() or "")
    return "\n".join(text_parts)


def _parse_docx(content: bytes) -> str:
    doc = Document(io.BytesIO(content))
    return "\n".join(para.text for para in doc.paragraphs if para.text.strip())
