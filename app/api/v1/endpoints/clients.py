"""Client configuration CRUD endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ClientConfig
from app.db.session import get_db
from app.schemas.client_config import (
    ClientConfigCreate,
    ClientConfigRead,
    ClientConfigUpdate,
)

router = APIRouter(tags=["clients"])


@router.post(
    "/",
    response_model=ClientConfigRead,
    status_code=status.HTTP_201_CREATED,
    summary="Onboard a new client (job_roles from Job Roles API)",
)
async def create_client(
    payload: ClientConfigCreate,
    db: AsyncSession = Depends(get_db),
):
    # Check for duplicate client_id
    existing = await db.execute(
        select(ClientConfig).where(ClientConfig.client_id == payload.client_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Client '{payload.client_id}' already exists",
        )

    client = ClientConfig(
        client_id=payload.client_id,
        client_name=payload.client_name,
        default_source=payload.default_source.value,
        default_shared_filters=payload.default_shared_filters.model_dump(exclude_none=True),
        default_ats_filters=(
            payload.default_ats_filters.model_dump(exclude_none=True)
            if payload.default_ats_filters
            else None
        ),
        default_linkedin_filters=(
            payload.default_linkedin_filters.model_dump(exclude_none=True)
            if payload.default_linkedin_filters
            else None
        ),
        job_roles=payload.job_roles,
    )
    db.add(client)
    await db.commit()
    await db.refresh(client)
    return client


@router.get(
    "/{client_id}",
    response_model=ClientConfigRead,
    summary="Get client configuration",
)
async def get_client(
    client_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ClientConfig).where(ClientConfig.client_id == client_id)
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client '{client_id}' not found",
        )
    return client


@router.put(
    "/{client_id}",
    response_model=ClientConfigRead,
    summary="Update client configuration",
)
async def update_client(
    client_id: str,
    payload: ClientConfigUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ClientConfig).where(ClientConfig.client_id == client_id)
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client '{client_id}' not found",
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "default_source" and value is not None:
            setattr(client, field, value.value if hasattr(value, "value") else value)
        elif field == "default_shared_filters" and value is not None:
            setattr(client, field, value.model_dump(exclude_none=True) if hasattr(value, "model_dump") else value)
        elif field == "default_ats_filters" and value is not None:
            setattr(client, field, value.model_dump(exclude_none=True) if hasattr(value, "model_dump") else value)
        elif field == "default_linkedin_filters" and value is not None:
            setattr(client, field, value.model_dump(exclude_none=True) if hasattr(value, "model_dump") else value)
        else:
            setattr(client, field, value)

    await db.commit()
    await db.refresh(client)
    return client


@router.delete(
    "/{client_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete client configuration",
)
async def delete_client(
    client_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ClientConfig).where(ClientConfig.client_id == client_id)
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client '{client_id}' not found",
        )
    await db.delete(client)
    await db.commit()
