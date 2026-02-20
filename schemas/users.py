from datetime import datetime
from typing import Annotated

from fastapi import status
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from core.enums import CurrencyEnum, UserStatusEnum
from exceptions.common_exceptions import BadRequestDataException


class RequestUserModel(BaseModel):
    email: Annotated[EmailStr, Field(max_length=100)]

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: str):
        if not isinstance(value, str):
            return value

        cleaned_value = "".join(value.strip().split())
        if len(cleaned_value) == 0:
            raise BadRequestDataException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Email can't consist entirely of spaces"
            )

        return cleaned_value


class RequestUserUpdateModel(BaseModel):
    status: UserStatusEnum


class ResponseUserBalanceModel(BaseModel):
    currency: CurrencyEnum | None = None
    amount: float | None = None


class ResponseUserModel(BaseModel):
    id: int
    email: str | None = None
    status: UserStatusEnum | None = None
    created: datetime | None = None
    balances: list[ResponseUserBalanceModel] | None = None


class UserModel(BaseModel):
    id: int
    email: str
    status: UserStatusEnum
    created: datetime
    updated: datetime
    model_config = ConfigDict(from_attributes=True)
