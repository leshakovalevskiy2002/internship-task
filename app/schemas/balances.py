from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.core.enums import CurrencyEnum


class UserBalanceResponse(BaseModel):
    currency: CurrencyEnum
    amount: Decimal

    model_config = ConfigDict(from_attributes=True)
