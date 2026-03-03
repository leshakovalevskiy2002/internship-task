from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.enums import CurrencyEnum, UserStatusEnum


class RequestUserModel(BaseModel):
    email: Annotated[EmailStr, Field(max_length=100)]

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: str):
        if not isinstance(value, str):
            return value

        cleaned_value = "".join(value.strip().split())
        if len(cleaned_value) == 0:
            raise ValueError("Email can't consist entirely of spaces")

        return cleaned_value


class RequestUserUpdateModel(BaseModel):
    status: UserStatusEnum


class ResponseUserBalanceModel(BaseModel):
    currency: CurrencyEnum
    amount: Annotated[Decimal, Field(ge=0, max_digits=15, decimal_places=2)]
    model_config = ConfigDict(from_attributes=True)


class ResponseUserModel(BaseModel):
    id: int
    email: str
    status: UserStatusEnum
    created: datetime
    balances: list[ResponseUserBalanceModel]
    model_config = ConfigDict(from_attributes=True)


class UserModel(BaseModel):
    id: int
    email: str
    status: UserStatusEnum
    created: datetime
    updated: datetime
    model_config = ConfigDict(from_attributes=True)
