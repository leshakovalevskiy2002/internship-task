from datetime import datetime
from decimal import Decimal
from uuid import UUID

import pytest_asyncio

from app.core.enums import CurrencyEnum, TransactionTypeEnum
from app.models.transaction import Transaction
from app.models.user import User


@pytest_asyncio.fixture
async def transaction_factory(session, user_factory):
    async def factory(
        user: User | None = None,
        operation_type: TransactionTypeEnum = TransactionTypeEnum.DEPOSIT,
        amount: Decimal = Decimal("100"),
        currency: CurrencyEnum = CurrencyEnum.USD,
        created: datetime | None = None,
        reversal_of_id: UUID | None = None,
    ):
        if user is None:
            user = await user_factory()

        transaction = Transaction(
            user_id=user.id,
            operation_type=operation_type,
            amount=amount,
            currency=currency,
            reversal_of_id=reversal_of_id,
        )

        if created is not None:
            transaction.created = created

        session.add(transaction)
        await session.flush()
        await session.refresh(transaction)

        return transaction

    return factory
