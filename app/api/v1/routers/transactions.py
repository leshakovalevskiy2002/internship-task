from datetime import datetime, timedelta
from typing import Annotated
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_async_session
from app.repositories.queries import (
    get_not_roll_backed_deposit_amount,
    get_not_roll_backed_transactions_count,
    get_not_roll_backed_withdraw_amount,
    get_registered_and_deposit_users_count,
    get_registered_and_not_roll_backed_deposit_users_count,
    get_registered_users_count,
    get_transactions_count,
)
from app.schemas.transactions import RequestTransactionModel, TransactionModel
from app.services.transactions_service import TransactionService

router = APIRouter(tags=["transactions"])


@router.get("/transactions", response_model=list[TransactionModel], status_code=status.HTTP_200_OK)
async def get_transactions(session: Annotated[AsyncSession, Depends(get_async_session)], user_id: UUID | None = None):
    transaction_service = TransactionService(session)
    transactions = await transaction_service.get_all_transactions(user_id=user_id)
    return transactions


@router.post("/{user_id}/transactions", response_model=TransactionModel, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    user_id: UUID,
    transaction: RequestTransactionModel,
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    transaction_service = TransactionService(session)
    return await transaction_service.create_transaction(
        user_id=user_id,
        currency=transaction.currency,
        amount=transaction.amount,
    )


@router.patch("/{user_id}/transactions/{transaction_id}", response_model=TransactionModel)
async def rollback_transaction(
    user_id: UUID,
    transaction_id: UUID,
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    transaction_service = TransactionService(session)
    return await transaction_service.rollback_transaction(transaction_id=transaction_id, user_id=user_id)


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
