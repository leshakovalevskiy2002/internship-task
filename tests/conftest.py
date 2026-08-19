import asyncio

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.community.redis import RedisContainer

from app.config.app import app
from app.config.redis import create_redis
from app.config.settings import get_database_settings
from app.dependencies import get_async_session, get_session_maker
from app.models.base import Base
from app.repositories.balances import BalanceRepository
from app.repositories.reports import ReportRepository
from app.repositories.transactions import TransactionRepository
from app.repositories.users import UserRepository
from app.uow import UnitOfWork

pytest_plugins = [
    "tests.fixtures.users",
    "tests.fixtures.transactions",
    "tests.fixtures.balances",
]


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def db_settings():
    return get_database_settings()


@pytest_asyncio.fixture(scope="session")
async def engine(db_settings):
    test_engine = create_async_engine(
        db_settings.url, echo=False, connect_args={"server_settings": {"timezone": "UTC"}}
    )

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield test_engine

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await test_engine.dispose()


@pytest.fixture(scope="session")
def session_maker(engine):
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def clean_db(session_maker):
    async with session_maker() as cleanup_session:
        for table in reversed(Base.metadata.sorted_tables):
            await cleanup_session.execute(table.delete())
        await cleanup_session.commit()


@pytest.fixture
def uow(session_maker):
    return UnitOfWork(session_maker)


@pytest_asyncio.fixture
async def session(session_maker):
    async with session_maker() as test_session:
        yield test_session


@pytest_asyncio.fixture
async def app_test(session, session_maker):
    async def _get_async_session():
        yield session

    def _get_session_maker():
        return session_maker

    app.dependency_overrides[get_async_session] = _get_async_session
    app.dependency_overrides[get_session_maker] = _get_session_maker

    yield app

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(app_test: FastAPI):
    transport = ASGITransport(app=app_test)  # type: ignore[arg-type]

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture(scope="session")
def redis_container():
    with RedisContainer("redis:8") as container:
        host = container.get_container_host_ip()
        port = container.get_exposed_port(6379)

        yield host, port


@pytest_asyncio.fixture
async def redis(redis_container, monkeypatch):
    host, port = redis_container

    monkeypatch.setenv("REDIS_HOST", host)
    monkeypatch.setenv("REDIS_PORT", str(port))

    client = create_redis()
    await client.flushdb()

    yield client

    await client.flushdb()
    await client.aclose()


@pytest_asyncio.fixture
async def app_with_redis(app_test, redis):
    app_test.state.redis = redis
    return app_test


@pytest_asyncio.fixture
async def client_with_redis(app_with_redis):
    transport = ASGITransport(app=app_with_redis)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def user_repository(session: AsyncSession):
    return UserRepository(session=session)


@pytest.fixture
def balance_repository(session: AsyncSession):
    return BalanceRepository(session=session)


@pytest.fixture
def transaction_repository(session: AsyncSession):
    return TransactionRepository(session=session)


@pytest.fixture
def report_repository(session: AsyncSession):
    return ReportRepository(session=session)
