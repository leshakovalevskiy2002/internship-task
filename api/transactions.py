from datetime import datetime, timedelta
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, status
from sqlalchemy import ScalarResult, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.enums import TransactionStatusEnum, UserStatusEnum
from database import get_async_session
from exceptions import transaction_exceptions
from exceptions.common_exceptions import BadRequestDataException
from exceptions.user_exceptions import NegativeBalanceException, UserNotExistsException
from models.balance import UserBalance
from models.transaction import Transaction
from models.user import User
from queries import (
    get_not_roll_backed_deposit_amount,
    get_not_roll_backed_withdraw_amount,
    get_not_roll_backed_transactions_count,
    get_registered_and_deposit_users_count,
    get_registered_and_not_roll_backed_deposit_users_count,
    get_registered_users_count,
    get_transactions_count,
)
from schemas.transactions import RequestTransactionModel, TransactionModel

router = APIRouter(tags=["transactions"])


@router.get("/transactions", response_model=list[TransactionModel], status_code=status.HTTP_200_OK)
async def get_transactions(
    session: Annotated[AsyncSession, Depends(get_async_session)], user_id: int | None = None
) -> ScalarResult[Transaction]:
    query = select(Transaction).order_by(Transaction.created.desc())
    if user_id:
        query = query.where(Transaction.user_id == user_id)

    result = await session.execute(query)
    transactions = result.scalars()
    return transactions


@router.post("/{user_id}/transactions", response_model=TransactionModel, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    user_id: int, transaction: RequestTransactionModel, session: Annotated[AsyncSession, Depends(get_async_session)]
):
    if user_id <= 0:
        raise BadRequestDataException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unprocessable data in request"
        )

    result = await session.execute(select(User).where(User.id == user_id))
    db_user = result.scalar()
    if not db_user:
        raise UserNotExistsException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id=`{user_id}` does not exist"
        )
    if db_user.status != UserStatusEnum.ACTIVE:
        raise transaction_exceptions.CreateTransactionForBlockedUserException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id=`{user_id}` is blocked"
        )

    result = await session.execute(
        select(UserBalance).where(UserBalance.user_id == user_id, UserBalance.currency == transaction.currency)
    )
    db_user_balance = result.scalar()

    if db_user_balance.amount + transaction.amount < 0:
        raise NegativeBalanceException(status_code=status.HTTP_400_BAD_REQUEST, detail="Negative balance")

    db_user_balance.amount += transaction.amount
    new_transaction = Transaction(user_id=user_id, **transaction.model_dump())
    session.add(new_transaction)
    await session.commit()
    await session.refresh(new_transaction)
    return new_transaction


@router.patch("/{user_id}/transactions/{transaction_id}", response_model=TransactionModel)
async def rollback_transaction(
    user_id: int, transaction_id: int, session: Annotated[AsyncSession, Depends(get_async_session)]
):
    if user_id <= 0 or transaction_id <= 0:
        raise BadRequestDataException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unprocessable data in request"
        )
    result = await session.execute(select(User).where(User.id == user_id))
    db_user = result.scalar()
    if not db_user:
        raise UserNotExistsException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id=`{user_id}` does not exist"
        )
    result = await session.execute(select(Transaction).where(Transaction.id == transaction_id))
    db_transaction = result.scalar()
    if not db_transaction:
        raise transaction_exceptions.TransactionNotExistsException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Transaction with id=`{transaction_id}` does not exist"
        )

    if db_transaction.user_id != db_user.id:
        raise transaction_exceptions.TransactionDoesNotBelongToUserException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transaction with id=`{transaction_id}` does not belong to user with id=`{user_id}`",
        )
    if db_transaction.status == TransactionStatusEnum.ROLL_BACKED:
        raise transaction_exceptions.TransactionAlreadyRollbackedException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transaction with id=`{transaction_id}` is already rollbacked",
        )
    if db_user.status == UserStatusEnum.BLOCKED:
        raise transaction_exceptions.UpdateTransactionForBlockedUserException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"User with id=`{user_id}` is blocked"
        )

    result = await session.execute(
        select(UserBalance).where(UserBalance.user_id == user_id, UserBalance.currency == db_transaction.currency)
    )
    db_user_balance = result.scalar()

    user_balance_amount = db_user_balance.amount
    new_user_balance_amount = user_balance_amount - db_transaction.amount

    if new_user_balance_amount < 0:
        raise NegativeBalanceException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Negative balance: {new_user_balance_amount}"
        )

    db_transaction.status = TransactionStatusEnum.ROLL_BACKED
    db_user_balance.amount = new_user_balance_amount
    await session.commit()
    await session.refresh(db_transaction)
    return db_transaction


@router.get("/transactions/analysis", status_code=status.HTTP_200_OK)
async def get_transaction_analysis(session: Annotated[AsyncSession, Depends(get_async_session)]) -> list[dict]:
    datetime_now = datetime.now(ZoneInfo("UTC"))
    datetime_week_ago = datetime_now - timedelta(days=6)

    date_now = datetime_now.date()
    date_week_ago = datetime_week_ago.date()

    results = []
    for _ in range(52):
        registered_users_count = await get_registered_users_count(session, start_date=date_week_ago, end_date=date_now)
        registered_and_deposit_users_count = await get_registered_and_deposit_users_count(
            session, start_date=date_week_ago, end_date=date_now
        )
        registered_and_not_roll_backed_deposit_users_count = (
            await get_registered_and_not_roll_backed_deposit_users_count(
                session, start_date=date_week_ago, end_date=date_now
            )
        )
        not_roll_backed_deposit_amount = await get_not_roll_backed_deposit_amount(
            session, start_date=date_week_ago, end_date=date_now
        )
        not_roll_backed_withdraw_amount = await get_not_roll_backed_withdraw_amount(
            session, start_date=date_week_ago, end_date=date_now
        )
        transactions_count = await get_transactions_count(session, start_date=date_week_ago, end_date=date_now)
        not_roll_backed_transactions_count = await get_not_roll_backed_transactions_count(
            session, start_date=date_week_ago, end_date=date_now
        )
        result = {
            "start_date": date_week_ago,
            "end_date": date_now,
            "registered_users_count": registered_users_count,
            "registered_and_deposit_users_count": registered_and_deposit_users_count,
            "registered_and_not_roll_backed_deposit_users_count": registered_and_not_roll_backed_deposit_users_count,
            "not_roll_backed_deposit_amount": not_roll_backed_deposit_amount,
            "not_roll_backed_withdraw_amount": not_roll_backed_withdraw_amount,
            "transactions_count": transactions_count,
            "not_roll_backed_transactions_count": not_roll_backed_transactions_count,
        }
        results.append(result)
        date_week_ago -= timedelta(weeks=1)
        date_now -= timedelta(weeks=1)
    return results
