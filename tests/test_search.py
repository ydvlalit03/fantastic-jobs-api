"""Tests for the search endpoint."""

from unittest.mock import AsyncMock, patch

import pytest

from app.schemas.response import NormalizedJob


def _mock_job(title="Engineer", org="Acme", source="ats"):
    return NormalizedJob(
        id="1",
        title=title,
        organization=org,
        source_api=source,
        source_platform=source,
    )


@pytest.mark.asyncio
@patch("app.services.fantastic_jobs.search_orchestrator.ATSClient")
@patch("app.services.fantastic_jobs.search_orchestrator.LinkedInClient")
async def test_search_with_titles(mock_li_cls, mock_ats_cls, client):
    mock_ats = AsyncMock()
    mock_ats.search.return_value = [
        {"id": "1", "title": "Engineer", "organization": "Acme"}
    ]
    mock_ats_cls.return_value = mock_ats

    mock_li = AsyncMock()
    mock_li.search.return_value = [
        {"id": "2", "title": "Engineer", "organization": "BigCo"}
    ]
    mock_li_cls.return_value = mock_li

    payload = {"titles": ["Software Engineer"], "source": "ats"}
    response = await client.post("/api/v1/search", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "jobs" in data
    assert data["sources_queried"] == ["ats"]


@pytest.mark.asyncio
async def test_search_without_titles_or_client(client):
    payload = {"source": "ats"}
    response = await client.post("/api/v1/search", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_search_with_nonexistent_client(client):
    payload = {"client_id": "no-such-client"}
    response = await client.post("/api/v1/search", json=payload)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_search_title_filter_mutual_exclusion(client):
    payload = {
        "titles": ["Engineer"],
        "title_filter": "foo",
        "advanced_title_filter": "bar",
    }
    response = await client.post("/api/v1/search", json=payload)
    assert response.status_code == 422
