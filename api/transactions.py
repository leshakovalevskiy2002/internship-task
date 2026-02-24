from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy import ScalarResult, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.enums import CurrencyEnum
from database import get_async_session
from exceptions import transaction_exceptions
from exceptions.common_exceptions import BadRequestDataException
from exceptions.user_exceptions import NegativeBalanceException, UserNotExistsException
from models.balance import UserBalance
from models.transaction import Transaction
from models.user import User
from queries import (
    get_not_rollbacked_deposit_amount,
    get_not_rollbacked_transactions_count,
    get_not_rollbacked_withdraw_amount,
    get_registered_and_deposit_users_count,
    get_registered_and_not_rollbacked_deposit_users_count,
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


@router.post("/{user_id}/transactions", response_model=TransactionModel | None, status_code=status.HTTP_200_OK)
async def post_transaction(
    user_id: int, transaction: RequestTransactionModel, session: AsyncSession = Depends(get_async_session)
):
    if user_id < 0:
        raise BadRequestDataException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unprocessable data in request"
        )
    if transaction.currency not in {str(x) for x in CurrencyEnum}:
        raise BadRequestDataException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Currency does not exist"
        )
    if transaction.amount == 0:
        raise BadRequestDataException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Transaction can not have zero amount"
        )

    db_user = await session.execute(select(User).where(User.id == user_id))
    db_user = db_user.scalar()
    if not db_user:
        raise UserNotExistsException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User with id=`{0}` does not exist".format(user_id)
        )
    if db_user.status != "ACTIVE":
        raise transaction_exceptions.CreateTransactionForBlockedUserException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User with id=`{0}` is blocked".format(user_id)
        )

    db_user_balance = await session.execute(
        select(UserBalance).where((UserBalance.user_id == user_id) & (UserBalance.currency == transaction.currency))
    )
    db_user_balance = db_user_balance.scalar()
    if float(db_user_balance.amount) + transaction.amount < 0:
        raise NegativeBalanceException(status_code=status.HTTP_400_BAD_REQUEST, detail="Negative balance")

    await session.execute(
        update(UserBalance).values(**{"amount": transaction.amount}).where(UserBalance.id == db_user_balance.id)
    )
    await session.commit()
    await session.execute(
        insert(Transaction).values(
            **{
                "user_id": db_user.id,
                "currency": transaction.currency,
                "amount": transaction.amount,
                "status": "PROCESSED",
                "created": datetime.utcnow(),
            }
        )
    )
    await session.commit()


@router.patch("/{user_id}/transactions/{transaction_id}", response_model=TransactionModel | None)
async def patch_rollback_transaction(
    user_id: int, transaction_id: int, session: AsyncSession = Depends(get_async_session)
):
    if user_id < 0 or transaction_id < 0:
        raise BadRequestDataException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unprocessable data in request"
        )
    db_user = await session.execute(select(User).where(User.id == user_id))
    db_user = db_user.scalar()
    if not db_user:
        raise UserNotExistsException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User with id=`{0}` does not exist".format(user_id)
        )
    db_transaction = await session.execute(select(Transaction).where(Transaction.id == transaction_id))
    db_transaction = db_transaction.scalar()
    if not db_transaction:
        raise transaction_exceptions.TransactionNotExistsException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaction with id=`{0}` does not exist".format(transaction_id),
        )
    if db_transaction.user_id != db_user.id:
        raise transaction_exceptions.TransactionDoesNotBelongToUserException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaction with id=`{0}` does not belong to user with id=`{1}`".format(transaction_id, user_id),
        )
    if db_transaction.status == "ROLLBACKED":
        raise transaction_exceptions.TransactionAlreadyRollbackedException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaction with id=`{0}` is already rollbacked".format(transaction_id),
        )
    if db_user.status == "BLOCKED":
        raise transaction_exceptions.UpdateTransactionForBlockedUserException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User with id=`{0}` is blocked".format(user_id)
        )

    db_user_balance = await session.execute(
        select(UserBalance).where((UserBalance.user_id == user_id) & (UserBalance.currency == db_transaction.currency))
    )
    db_user_balance = db_user_balance.scalar()
    new_amount = float(db_user_balance.amount)
    if db_transaction.amount < 0:
        new_amount += abs(float(db_transaction.amount))
    else:
        new_amount -= float(db_transaction.amount)
    if new_amount < 0:
        raise NegativeBalanceException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Negative balance: {new_amount}"
        )
    await session.execute(
        update(UserBalance).values(**{"amount": new_amount}).where(UserBalance.id == db_user_balance.id)
    )
    await session.commit()
    await session.execute(update(Transaction).values(**{"status": "ROLLBACKED"}))
    await session.commit()


@router.get("/transactions/analysis", response_model=list[dict] | None, status_code=status.HTTP_200_OK)
async def get_transaction_analysis(session: AsyncSession = Depends(get_async_session)) -> list[dict]:
    dt_gt = datetime.utcnow().date() - timedelta(weeks=1) + timedelta(days=1)
    dt_lt = datetime.utcnow().date()
    results = []
    for i in range(52):
        registered_users_count = await get_registered_users_count(session, dt_gt=dt_gt, dt_lt=dt_lt)
        registered_and_deposit_users_count = await get_registered_and_deposit_users_count(
            session, dt_gt=dt_gt, dt_lt=dt_lt
        )
        registered_and_not_rollbacked_deposit_users_count = await get_registered_and_not_rollbacked_deposit_users_count(
            session, dt_gt=dt_gt, dt_lt=dt_lt
        )
        not_rollbacked_deposit_amount = await get_not_rollbacked_deposit_amount(session, dt_gt=dt_gt, dt_lt=dt_lt)
        not_rollbacked_withdraw_amount = await get_not_rollbacked_withdraw_amount(session, dt_gt=dt_gt, dt_lt=dt_lt)
        transactions_count = await get_transactions_count(session, dt_gt=dt_gt, dt_lt=dt_lt)
        not_rollbacked_transactions_count = await get_not_rollbacked_transactions_count(
            session, dt_gt=dt_gt, dt_lt=dt_lt
        )
        result = {
            "start_date": dt_gt,
            "end_date": dt_lt,
            "registered_users_count": registered_users_count,
            "registered_and_deposit_users_count": registered_and_deposit_users_count,
            "registered_and_not_rollbacked_deposit_users_count": registered_and_not_rollbacked_deposit_users_count,
            "not_rollbacked_deposit_amount": not_rollbacked_deposit_amount,
            "not_rollbacked_withdraw_amount": not_rollbacked_withdraw_amount,
            "transactions_count": transactions_count,
            "not_rollbacked_transactions_count": not_rollbacked_transactions_count,
        }
        for field in (
            "registered_users_count",
            "registered_and_deposit_users_count",
            "registered_and_not_rollbacked_deposit_users_count",
            "not_rollbacked_deposit_amount",
            "not_rollbacked_withdraw_amount",
            "transactions_count",
            "not_rollbacked_transactions_count",
        ):
            if result[field] > 0:
                results.append(result)
                break
        dt_gt -= timedelta(weeks=1)
        dt_lt -= timedelta(weeks=1)
    return results
