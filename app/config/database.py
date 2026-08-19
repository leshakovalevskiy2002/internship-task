from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.config.settings import get_database_settings
from app.models.base import Base


@lru_cache
def get_engine() -> AsyncEngine:
    settings = get_database_settings()
    return create_async_engine(settings.url, echo=True, connect_args={"server_settings": {"timezone": "UTC"}})


@lru_cache
def create_session_maker(db_engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=db_engine, class_=AsyncSession, expire_on_commit=False)


engine = get_engine()
async_session_maker = create_session_maker(engine)


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
