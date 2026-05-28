"""Tests for the POST /api/v1/job-search endpoint."""

from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
@patch("app.api.v1.endpoints.job_search._call_api")
async def test_linkedin_search(mock_call, client):
    mock_call.return_value = [
        {"id": "1", "title": "Program Manager", "organization": "Google"},
        {"id": "2", "title": "Salesforce Consultant", "organization": "Deloitte"},
    ]

    payload = {
        "type": "LINKEDIN",
        "advanced_title_filter": ["Program Manager", "Salesforce Consultant"],
        "limit": 10,
        "include_ai": True,
    }
    response = await client.post("/api/v1/job-search", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["sources_queried"] == ["linkedin"]
    assert data["total_results"] == 2
    assert data["jobs"][0]["title"] == "Program Manager"
    assert data["jobs"][0]["source_api"] == "linkedin"


@pytest.mark.asyncio
@patch("app.api.v1.endpoints.job_search._call_api")
async def test_ats_search(mock_call, client):
    mock_call.return_value = [
        {"id": "10", "title": "Business Architect", "organization": "Acme", "source": "greenhouse"},
    ]

    payload = {
        "type": "ATS_CAREER_SITES",
        "advanced_title_filter": ["Business Architect"],
        "limit": 15,
    }
    response = await client.post("/api/v1/job-search", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["sources_queried"] == ["ats"]
    assert data["total_results"] == 1
    assert data["jobs"][0]["source_api"] == "ats"


@pytest.mark.asyncio
@patch("app.api.v1.endpoints.job_search._call_api")
async def test_search_with_all_filters(mock_call, client):
    mock_call.return_value = []

    payload = {
        "type": "LINKEDIN",
        "advanced_title_filter": ["Program Manager"],
        "limit": 10,
        "location_filter": ["Atlanta", "Seattle", "Dallas"],
        "type_filter": "CONTRACTOR",
        "remote": True,
        "agency": True,
        "industry_filter": "Technology",
        "date_filter": "2025-01-01",
        "exclude_ats_duplicate": True,
        "include_ai": True,
    }
    response = await client.post("/api/v1/job-search", json=payload)
    assert response.status_code == 200
    assert response.json()["total_results"] == 0


@pytest.mark.asyncio
async def test_missing_type_returns_422(client):
    payload = {"advanced_title_filter": ["Engineer"]}
    response = await client.post("/api/v1/job-search", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_missing_titles_returns_422(client):
    payload = {"type": "LINKEDIN"}
    response = await client.post("/api/v1/job-search", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_empty_titles_returns_422(client):
    payload = {"type": "LINKEDIN", "advanced_title_filter": []}
    response = await client.post("/api/v1/job-search", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_invalid_type_returns_422(client):
    payload = {"type": "INVALID", "advanced_title_filter": ["Engineer"]}
    response = await client.post("/api/v1/job-search", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_invalid_type_filter_returns_422(client):
    payload = {
        "type": "LINKEDIN",
        "advanced_title_filter": ["Engineer"],
        "type_filter": "INVALID_TYPE",
    }
    response = await client.post("/api/v1/job-search", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
@patch("app.api.v1.endpoints.job_search._call_api")
async def test_response_has_metadata(mock_call, client):
    mock_call.return_value = [
        {"id": "1", "title": "Engineer", "organization": "Co"},
    ]

    payload = {
        "type": "ATS_CAREER_SITES",
        "advanced_title_filter": ["Engineer"],
    }
    response = await client.post("/api/v1/job-search", json=payload)
    data = response.json()
    assert "metadata" in data
    assert "elapsed_seconds" in data["metadata"]
    assert data["page"] == 1
    assert data["page_size"] == 10


@pytest.mark.asyncio
@patch("app.api.v1.endpoints.job_search._call_api")
async def test_dict_response_format(mock_call, client):
    """API sometimes returns {data: [...]} instead of a plain list."""
    mock_call.return_value = {
        "data": [
            {"id": "1", "title": "PM", "organization": "X"},
        ]
    }

    payload = {
        "type": "LINKEDIN",
        "advanced_title_filter": ["PM"],
    }
    response = await client.post("/api/v1/job-search", json=payload)
    assert response.status_code == 200
    assert response.json()["total_results"] == 1
