from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import CurrencyEnum
from app.models.balance import UserBalance


class BalanceRepository:
    def __init__(self, session: AsyncSession):
        self.session: AsyncSession = session

    async def create_default_balances_for_user(self, user_id: UUID) -> None:
        for currency in CurrencyEnum:
            self.session.add(UserBalance(user_id=user_id, currency=currency))

    async def get_user_balance(self, user_id: UUID, currency: CurrencyEnum) -> UserBalance | None:
        query = select(UserBalance).where(UserBalance.user_id == user_id, UserBalance.currency == currency)
        result = await self.session.scalars(query)
        return result.one_or_none()

    async def update_balance_amount(self, user_balance: UserBalance, new_amount: Decimal) -> UserBalance:
        user_balance.amount = new_amount
        await self.session.flush()
        return user_balance
