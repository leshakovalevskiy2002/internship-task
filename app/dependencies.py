from typing import Annotated, AsyncIterator, cast

from fastapi import Depends, Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.repositories.transactions import TransactionRepository
from app.repositories.users import UserRepository
from app.services.report_query_service import ReportService
from app.services.transactions_service import TransactionService
from app.services.users_service import UserService
from app.uow import UnitOfWork


async def get_redis(request: Request) -> Redis:
    redis = getattr(request.app.state, "redis", None)
    if redis is None:
        raise RuntimeError("Redis is not initialized")
    return cast(Redis, redis)


async def get_session_maker(request: Request) -> async_sessionmaker[AsyncSession]:
    session_maker = getattr(request.app.state, "session_maker", None)
    if session_maker is None:
        raise RuntimeError("Database is not initialized")
    return cast(async_sessionmaker[AsyncSession], session_maker)


async def get_session(
    session_maker: Annotated[async_sessionmaker[AsyncSession], Depends(get_session_maker)]
) -> AsyncIterator[AsyncSession]:
    async with session_maker() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_uow(session_maker: Annotated[async_sessionmaker[AsyncSession], Depends(get_session_maker)]) -> UnitOfWork:
    return UnitOfWork(session_maker)


async def get_user_repo(session: SessionDep) -> UserRepository:
    return UserRepository(session)


async def get_transaction_repo(session: SessionDep) -> TransactionRepository:
    return TransactionRepository(session)


async def get_user_service(uow: Annotated[UnitOfWork, Depends(get_uow)]) -> UserService:
    return UserService(uow=uow)


async def get_transaction_service(uow: Annotated[UnitOfWork, Depends(get_uow)]) -> TransactionService:
    return TransactionService(uow=uow)


async def get_report_query_service(redis: Annotated[Redis, Depends(get_redis)]) -> ReportService:
    return ReportService(redis=redis)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
TransactionServiceDep = Annotated[TransactionService, Depends(get_transaction_service)]
