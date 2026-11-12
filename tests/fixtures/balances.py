from decimal import Decimal

import pytest_asyncio

from app.core.enums import CurrencyEnum
from app.models.balance import UserBalance
from app.models.user import User


@pytest_asyncio.fixture
async def user_balance_factory(session, user_factory):
    async def factory(
        user: User | None = None,
        currency: CurrencyEnum = CurrencyEnum.USD,
        amount: Decimal = Decimal("0.00"),
    ):
        if user is None:
            user = await user_factory()

        balance = UserBalance(user_id=user.id, currency=currency, amount=amount)
        session.add(balance)
        await session.flush()

        await session.refresh(balance)
        return balance

    return factory
