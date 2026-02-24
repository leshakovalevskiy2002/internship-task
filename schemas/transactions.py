from datetime import datetime
from decimal import Decimal
from typing import Annotated

from fastapi import status
from pydantic import BaseModel, ConfigDict, Field, field_validator

from core.enums import CurrencyEnum, TransactionStatusEnum
from exceptions.common_exceptions import BadRequestDataException


class RequestTransactionModel(BaseModel):
    currency: CurrencyEnum
    amount: Annotated[Decimal, Field(max_digits=15, decimal_places=2, examples=[Decimal("12345.67")])]

    @field_validator("currency", mode="before")
    @classmethod
    def check_currency_value(cls, value: str):
        if not isinstance(value, str):
            return value

        if value not in {str(x) for x in CurrencyEnum}:
            raise BadRequestDataException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Currency does not exist"
            )
        return value

    @field_validator("amount", mode="after")
    @classmethod
    def non_zero_amount_validation(cls, value: Decimal):
        if value == 0:
            raise BadRequestDataException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Transaction can not have zero amount"
            )
        return value


class TransactionModel(BaseModel):
    id: int
    user_id: int
    currency: CurrencyEnum
    amount: Annotated[Decimal, Field(max_digits=15, decimal_places=2, examples=[Decimal("12345.67")])]
    status: TransactionStatusEnum
    created: datetime
    updated: datetime

    model_config = ConfigDict(from_attributes=True)
