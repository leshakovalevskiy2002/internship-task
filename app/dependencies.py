from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import async_session_maker, get_async_session
from app.repositories.transactions import TransactionRepository
from app.repositories.users import UserRepository
from app.services.transactions_service import TransactionService
from app.services.users_service import UserService
from app.uow import UnitOfWork


def get_uow() -> UnitOfWork:
    return UnitOfWork(async_session_maker)


def get_user_repo(session: Annotated[AsyncSession, Depends(get_async_session)]) -> UserRepository:
    return UserRepository(session)


def get_transaction_repo(session: Annotated[AsyncSession, Depends(get_async_session)]) -> TransactionRepository:
    return TransactionRepository(session)


def get_user_service(uow: Annotated[UnitOfWork, Depends(get_uow)]) -> UserService:
    return UserService(uow=uow)


def get_transaction_service(uow: Annotated[UnitOfWork, Depends(get_uow)]) -> TransactionService:
    return TransactionService(uow=uow)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
TransactionServiceDep = Annotated[TransactionService, Depends(get_transaction_service)]
