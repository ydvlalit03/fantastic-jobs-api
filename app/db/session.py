from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()

# SQLite doesn't support pool_size/max_overflow
engine_kwargs: dict = {"echo": settings.DEBUG}
if "sqlite" not in settings.DATABASE_URL:
    engine_kwargs["pool_size"] = settings.DB_POOL_SIZE
    engine_kwargs["max_overflow"] = settings.DB_MAX_OVERFLOW

engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
