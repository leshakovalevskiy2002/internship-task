from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.enums import UserStatusEnum
from app.schemas.balances import UserBalanceResponse


class UserRegistrationRequest(BaseModel):
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


class BaseUserModel(BaseModel):
    id: UUID
    email: str
    status: UserStatusEnum
    created: datetime
    updated: datetime

    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseUserModel):
    pass


class UserWithBalancesResponse(BaseUserModel):
    balances: list[UserBalanceResponse]


class UpdateUserStatusRequest(BaseModel):
    status: UserStatusEnum
