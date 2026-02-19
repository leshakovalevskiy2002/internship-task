from pydantic import BaseModel
from pydantic.v1 import root_validator

from core.enums import CurrencyEnum


class UserBalanceModel(BaseModel):
    id: int
    user_id: int | None = None
    currency: CurrencyEnum | None = None
    amount: float | None = None

    @root_validator(pre=True)
    def validate_not_negative(self, values):
        if "amount" in values and values.get("amount"):
            if values["amount"] < 0:
                raise ValueError("Amount cannot be negative")

        return values
