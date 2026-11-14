from textwrap import dedent
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.dependencies import TransactionServiceDep, get_transaction_repo
from app.repositories.transactions import TransactionRepository
from app.schemas.transactions import CreateTransactionModel, TransactionModelResponse

router = APIRouter(tags=["transactions"])


@router.get(
    "/transactions",
    description=dedent(
        """
        Retrieves financial transactions, optionally filtered by user.

        **Filters:**
        - `user_id` — if provided, returns only transactions belonging to that user.
          If omitted, transactions for all users are returned.
        """
    ),
    response_model=list[TransactionModelResponse],
    status_code=status.HTTP_200_OK,
    summary="Get transactions",
)
async def get_transactions(
    transaction_repo: Annotated[TransactionRepository, Depends(get_transaction_repo)],
    user_id: UUID | None = None,
):
    return await transaction_repo.get_transactions(user_id=user_id)


@router.post(
    "/{user_id}/transactions",
    description=dedent(
        """
        Creates a new financial transaction for a specific user account.
        
        **Behavior:**
        - `DEPOSIT` adds the amount to the user's balance.
        - `WITHDRAW` subtracts the amount from the user's balance.
        - `WITHDRAW` is rejected if it would result in a negative balance.
        - `REVERSAL` cannot be created directly (use the rollback operation instead).
        - A balance for the specified currency must exist before creating the transaction.
        - Blocked users cannot create transactions.
        """
    ),
    response_model=TransactionModelResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new transaction",
)
async def create_transaction(
    transaction_service: TransactionServiceDep,
    user_id: UUID,
    transaction: CreateTransactionModel,
):
    return await transaction_service.create_transaction(
        user_id=user_id,
        currency=transaction.currency,
        amount=transaction.amount,
        operation_type=transaction.operation_type,
    )


@router.patch(
    "/{user_id}/transactions/{transaction_id}",
    description=dedent(
        """
        Rolls back a financial transaction for a specific user account.

        Creates a new `REVERSAL` transaction linked to the original transaction
        (via `reversal_of_id`) and reverses its effect on the user's balance.
        The original transaction remains unchanged.

        **Behavior:**
        - For a `DEPOSIT`, the amount is subtracted from the user's balance.
        - For a `WITHDRAW`, the amount is added back to the user's balance.
        - A new transaction with `operation_type = REVERSAL` is created.
        - A transaction can only be rolled back once.
        """
    ),
    response_model=TransactionModelResponse,
    summary="Roll back transaction",
)
async def rollback_transaction(
    transaction_service: TransactionServiceDep,
    user_id: UUID,
    transaction_id: UUID,
):
    return await transaction_service.rollback_transaction(transaction_id=transaction_id, user_id=user_id)
