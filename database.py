from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config import DataBaseSettings, get_database_settings

database_settings: DataBaseSettings = get_database_settings()
DATABASE_URL = database_settings.url()
engine = create_async_engine(DATABASE_URL, echo=True)


class Base(DeclarativeBase):
    pass


async_session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
