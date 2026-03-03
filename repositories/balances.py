from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.enums import CurrencyEnum
from models.balance import UserBalance
from decimal import Decimal


class BalanceRepository:
    def __init__(self, session: AsyncSession):
        self.session: AsyncSession = session

    async def create_default_balances_for_user(self, user_id: int) -> None:
        for currency in CurrencyEnum:
            self.session.add(UserBalance(user_id=user_id, currency=currency))

    async def get_user_balance(self, user_id: int, currency: CurrencyEnum) -> UserBalance | None:
        result = await self.session.scalar(
            select(UserBalance).where(UserBalance.user_id == user_id, UserBalance.currency == currency)
        )
        return result

    async def update_balance_amount(self, user_balance: UserBalance, new_amount: Decimal) -> UserBalance:
        user_balance.amount = new_amount
        await self.session.flush()
        return user_balance
