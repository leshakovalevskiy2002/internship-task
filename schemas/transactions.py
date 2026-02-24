from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from core.enums import CurrencyEnum, TransactionStatusEnum


class RequestTransactionModel(BaseModel):
    currency: CurrencyEnum
    amount: float


class TransactionModel(BaseModel):
    id: int
    user_id: int
    currency: CurrencyEnum
    amount: Annotated[Decimal, Field(ge=0, max_digits=15, decimal_places=2)]
    status: TransactionStatusEnum
    created: datetime
    updated: datetime

    model_config = ConfigDict(from_attributes=True)
