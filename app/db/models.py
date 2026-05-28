from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ClientConfig(Base):
    __tablename__ = "client_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    client_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    client_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Default source preference
    default_source: Mapped[str] = mapped_column(String(20), default="both")

    # Default filters stored as JSON
    default_shared_filters: Mapped[dict] = mapped_column(JSON, default=dict)
    default_ats_filters: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    default_linkedin_filters: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Job roles (from Job Roles API, set once during onboarding)
    job_roles: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
