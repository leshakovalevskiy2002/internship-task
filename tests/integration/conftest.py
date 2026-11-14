import asyncio

import pytest_asyncio
from sqlalchemy import text

from alembic import command
from alembic.config import Config
from app.models.base import Base


@pytest_asyncio.fixture(autouse=True)
async def clean_db(session_maker):
    async with session_maker() as cleanup_session:
        for table in reversed(Base.metadata.sorted_tables):
            await cleanup_session.execute(table.delete())
        await cleanup_session.commit()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def prepared_db(db_settings, engine):
    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))

    def _upgrade():
        cfg = Config("alembic.ini")
        cfg.set_main_option("sqlalchemy.url", db_settings.url)
        command.upgrade(cfg, "head")

    await asyncio.to_thread(_upgrade)
    yield
