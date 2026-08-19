from typing import Annotated, AsyncGenerator

from fastapi import Depends, Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config.database import async_session_maker
from app.repositories.transactions import TransactionRepository
from app.repositories.users import UserRepository
from app.services.report_query_service import ReportService
from app.services.transactions_service import TransactionServiceRead, TransactionServiceWrite
from app.services.users_service import UserServiceRead, UserServiceWrite
from app.uow import UnitOfWork


class AppState:
    redis: Redis


def get_redis(request: Request) -> Redis:
    state: AppState = request.app.state
    return state.redis


def get_session_maker() -> async_sessionmaker[AsyncSession]:
    return async_session_maker


async def get_async_session(
    session_maker: Annotated[async_sessionmaker[AsyncSession], Depends(get_session_maker)]
) -> AsyncGenerator[AsyncSession, None]:
    async with session_maker() as session:
        yield session


def get_uow(session_maker: Annotated[async_sessionmaker[AsyncSession], Depends(get_session_maker)]) -> UnitOfWork:
    return UnitOfWork(session_maker)


def get_user_repo(session: Annotated[AsyncSession, Depends(get_async_session)]) -> UserRepository:
    return UserRepository(session)


def get_transaction_repo(session: Annotated[AsyncSession, Depends(get_async_session)]) -> TransactionRepository:
    return TransactionRepository(session)


def get_user_service_read(user_repo: Annotated[UserRepository, Depends(get_user_repo)]) -> UserServiceRead:
    return UserServiceRead(user_repo=user_repo)


def get_user_service_write(uow: Annotated[UnitOfWork, Depends(get_uow)]) -> UserServiceWrite:
    return UserServiceWrite(uow=uow)


def get_transaction_service_read(
    transaction_repo: Annotated[TransactionRepository, Depends(get_transaction_repo)]
) -> TransactionServiceRead:
    return TransactionServiceRead(transaction_repo=transaction_repo)


def get_transaction_service_write(uow: Annotated[UnitOfWork, Depends(get_uow)]) -> TransactionServiceWrite:
    return TransactionServiceWrite(uow=uow)


def get_report_query_service(redis: Annotated[Redis, Depends(get_redis)]) -> ReportService:
    return ReportService(redis=redis)
