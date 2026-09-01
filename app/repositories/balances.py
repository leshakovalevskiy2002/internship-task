from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import CurrencyEnum
from app.models.balance import UserBalance


class BalanceRepository:
    def __init__(self, session: AsyncSession):
        self.session: AsyncSession = session

    async def create_default_balances_for_user(self, user_id: UUID) -> None:
        balances = [UserBalance(user_id=user_id, currency=currency) for currency in CurrencyEnum]
        self.session.add_all(balances)

    async def get_user_balance_for_update(self, user_id: UUID, currency: CurrencyEnum) -> UserBalance | None:
        query = (
            select(UserBalance)
            .where(UserBalance.user_id == user_id, UserBalance.currency == currency)
            .with_for_update()
        )
        result = await self.session.scalars(query)
        return result.one_or_none()
