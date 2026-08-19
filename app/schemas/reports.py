from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class WeeklyReport(BaseModel):
    start_date: date
    end_date: date
    registered_users_count: int
    deposit_users_count: int
    not_roll_backed_deposit_amount: Decimal
    not_roll_backed_withdraw_amount: Decimal
    transactions_count: int
    not_roll_backed_transactions_count: int
