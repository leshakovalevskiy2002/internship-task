from datetime import datetime

from pydantic import BaseModel

from core.enums import CurrencyEnum, UserStatusEnum


class RequestUserModel(BaseModel):
    email: str


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
    email: str | None = None
    status: UserStatusEnum | None = None
    created: datetime | None = None
