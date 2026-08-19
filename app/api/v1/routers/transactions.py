from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.dependencies import get_transaction_service_read, get_transaction_service_write
from app.schemas.transactions import CreateTransactionModel, TransactionModelResponse
from app.services.transactions_service import TransactionServiceRead, TransactionServiceWrite

router = APIRouter(tags=["transactions"])


@router.get("/transactions", response_model=list[TransactionModelResponse], status_code=status.HTTP_200_OK)
async def get_transactions(
    transaction_service: Annotated[TransactionServiceRead, Depends(get_transaction_service_read)],
    user_id: UUID | None = None,
):
    return await transaction_service.get_transactions(user_id=user_id)


@router.post("/{user_id}/transactions", response_model=TransactionModelResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction_service: Annotated[TransactionServiceWrite, Depends(get_transaction_service_write)],
    user_id: UUID,
    transaction: CreateTransactionModel,
):
    return await transaction_service.create_transaction(
        user_id=user_id,
        currency=transaction.currency,
        amount=transaction.amount,
        operation_type=transaction.operation_type,
    )


@router.patch("/{user_id}/transactions/{transaction_id}", response_model=TransactionModelResponse)
async def rollback_transaction(
    transaction_service: Annotated[TransactionServiceWrite, Depends(get_transaction_service_write)],
    user_id: UUID,
    transaction_id: UUID,
):
    return await transaction_service.rollback_transaction(transaction_id=transaction_id, user_id=user_id)
