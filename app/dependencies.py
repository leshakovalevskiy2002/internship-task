from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import async_session_maker, get_async_session
from app.repositories.transactions import TransactionRepository
from app.repositories.users import UserRepository
from app.services.transactions_service import TransactionServiceRead, TransactionServiceWrite
from app.services.users_service import UserServiceRead, UserServiceWrite
from app.uow import UnitOfWork


def get_uow() -> UnitOfWork:
    return UnitOfWork(async_session_maker)


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
