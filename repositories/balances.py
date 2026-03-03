from sqlalchemy.ext.asyncio import AsyncSession

from core.enums import CurrencyEnum
from models.balance import UserBalance


class BalanceRepository:
    def __init__(self, session: AsyncSession):
        self.session: AsyncSession = session

    async def create_default_balances_for_user(self, user_id: int) -> None:
        for currency in CurrencyEnum:
            self.session.add(UserBalance(user_id=user_id, currency=currency))
