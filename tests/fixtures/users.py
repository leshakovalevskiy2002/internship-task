import random
import uuid
from datetime import datetime
from decimal import Decimal

import pytest_asyncio

from app.core.enums import CurrencyEnum, UserStatusEnum
from app.models.balance import UserBalance
from app.models.user import User


@pytest_asyncio.fixture
async def user_factory(session):
    async def factory(
        email: str | None = None,
        status: UserStatusEnum = UserStatusEnum.ACTIVE,
        created: datetime | None = None,
    ):
        if email is None:
            email = f"test_{uuid.uuid4()}@example.com"

        user = User(email=email, status=status)

        if created is not None:
            user.created = created

        session.add(user)
        await session.flush()
        await session.refresh(user)

        return user

    return factory


@pytest_asyncio.fixture
async def user_factory_with_balances(session, user_factory):
    async def factory(
        email: str | None = None,
        status: UserStatusEnum = UserStatusEnum.ACTIVE,
        generate_random_balances: bool = False,
    ):
        user = await user_factory(email=email, status=status)

        balances = [
            UserBalance(
                user_id=user.id,
                currency=currency,
                amount=(
                    Decimal("0.00")
                    if not generate_random_balances
                    else Decimal(random.randint(0, 10000)) / Decimal("100")
                ),
            )
            for currency in CurrencyEnum
        ]

        session.add_all(balances)

        await session.flush()
        await session.refresh(user)

        return user

    return factory


@pytest_asyncio.fixture
async def user_for_api(user_factory, session):
    async def factory(
        email: str | None = None,
        status: UserStatusEnum = UserStatusEnum.ACTIVE,
    ):
        user = await user_factory(email=email, status=status)

        await session.commit()

        return user

    return factory
