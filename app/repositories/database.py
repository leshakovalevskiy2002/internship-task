from collections.abc import AsyncGenerator
import re

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, declared_attr

from app.config.base import DataBaseSettings, get_database_settings
from app.models.base import BaseMixin

database_settings: DataBaseSettings = get_database_settings()
DATABASE_URL = database_settings.url()
engine = create_async_engine(DATABASE_URL, echo=True)


class Base(BaseMixin, DeclarativeBase):
    @classmethod
    @declared_attr.directive
    def __tablename__(cls) -> str:
        snake_name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", cls.__name__).lower()
        return snake_name if snake_name.endswith("s") else f"{snake_name}s"


async_session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("SET TIME ZONE 'UTC'"))
