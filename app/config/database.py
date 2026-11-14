import os

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.config.settings import get_database_settings


def create_engine() -> AsyncEngine:
    is_dev = os.getenv("MODE", "prod") == "dev"

    return create_async_engine(
        get_database_settings().url,
        echo=is_dev,
        connect_args={"server_settings": {"timezone": "UTC"}},
    )


def create_session_maker(db_engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=db_engine, class_=AsyncSession, expire_on_commit=False)
