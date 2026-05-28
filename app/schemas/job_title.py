"""Schemas for the Job Title suggestion service."""

from typing import Optional

from pydantic import BaseModel


class ContextInput(BaseModel):
    goal: str
    linkedinProfile: Optional[str] = None
    questionnaire: Optional[str] = None
    additionalInfo: Optional[str] = None


class TitleSuggestionItem(BaseModel):
    title: str
    description: str
    score: int


class TitleRequest(BaseModel):
    name: str
    id: str
    linkedinProfileUrl: str
    context: ContextInput


class TitleResponse(BaseModel):
    name: str
    id: str
    titles: list[TitleSuggestionItem]
