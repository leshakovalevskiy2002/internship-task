from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from app.core.enums import CurrencyEnum


class UserBalanceModel(BaseModel):
    id: UUID
    user_id: UUID
    currency: CurrencyEnum
    amount: Decimal

    model_config = ConfigDict(from_attributes=True)

    @field_validator("amount", mode="after")
    @classmethod
    def validate_not_negative(cls, value: Decimal):
        if value < 0:
            raise ValueError("Amount cannot be negative")
        return value
