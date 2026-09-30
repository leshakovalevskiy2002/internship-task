import pytest_asyncio

from app.models.base import Base


@pytest_asyncio.fixture(autouse=True)
async def clean_db(session_maker):
    async with session_maker() as cleanup_session:
        for table in reversed(Base.metadata.sorted_tables):
            await cleanup_session.execute(table.delete())
        await cleanup_session.commit()
