from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.enums import CurrencyEnum, TransactionStatusEnum, TransactionTypeEnum


class CreateTransactionModel(BaseModel):
    currency: CurrencyEnum
    amount: Annotated[Decimal, Field(max_digits=15, decimal_places=2, examples=[Decimal("12345.67")])]
    operation_type: TransactionTypeEnum

    @field_validator("amount", mode="after")
    @classmethod
    def positive_amount_validation(cls, value: Decimal):
        if value <= 0:
            raise ValueError("Transaction amount must be positive")
        return value


class TransactionModelResponse(BaseModel):
    id: UUID
    user_id: UUID
    currency: CurrencyEnum
    operation_type: TransactionTypeEnum
    amount: Decimal
    status: TransactionStatusEnum
    created: datetime
    updated: datetime

    model_config = ConfigDict(from_attributes=True)
