"""Tests for the client configuration CRUD endpoints."""

import pytest


@pytest.mark.asyncio
async def test_create_client(client):
    payload = {
        "client_id": "acme",
        "client_name": "Acme Corp",
        "job_roles": ["Software Engineer", "Data Scientist"],
    }
    response = await client.post("/api/v1/clients/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["client_id"] == "acme"
    assert data["client_name"] == "Acme Corp"
    assert data["job_roles"] == ["Software Engineer", "Data Scientist"]
    assert data["default_source"] == "both"


@pytest.mark.asyncio
async def test_create_duplicate_client(client):
    payload = {
        "client_id": "acme",
        "client_name": "Acme Corp",
        "job_roles": ["Engineer"],
    }
    await client.post("/api/v1/clients/", json=payload)
    response = await client.post("/api/v1/clients/", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_client(client):
    payload = {
        "client_id": "acme",
        "client_name": "Acme Corp",
        "job_roles": ["Engineer"],
    }
    await client.post("/api/v1/clients/", json=payload)
    response = await client.get("/api/v1/clients/acme")
    assert response.status_code == 200
    assert response.json()["client_id"] == "acme"


@pytest.mark.asyncio
async def test_get_nonexistent_client(client):
    response = await client.get("/api/v1/clients/nope")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_client(client):
    payload = {
        "client_id": "acme",
        "client_name": "Acme Corp",
        "job_roles": ["Engineer"],
    }
    await client.post("/api/v1/clients/", json=payload)

    update = {"client_name": "Acme Inc", "job_roles": ["Developer", "Designer"]}
    response = await client.put("/api/v1/clients/acme", json=update)
    assert response.status_code == 200
    data = response.json()
    assert data["client_name"] == "Acme Inc"
    assert data["job_roles"] == ["Developer", "Designer"]


@pytest.mark.asyncio
async def test_delete_client(client):
    payload = {
        "client_id": "acme",
        "client_name": "Acme Corp",
        "job_roles": ["Engineer"],
    }
    await client.post("/api/v1/clients/", json=payload)

    response = await client.delete("/api/v1/clients/acme")
    assert response.status_code == 204

    response = await client.get("/api/v1/clients/acme")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_nonexistent_client(client):
    response = await client.delete("/api/v1/clients/nope")
    assert response.status_code == 404
