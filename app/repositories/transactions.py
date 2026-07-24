from decimal import Decimal
from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import CurrencyEnum
from app.models.transaction import Transaction


class TransactionRepository:
    def __init__(self, session: AsyncSession):
        self.session: AsyncSession = session

    async def get_all_transactions(self, user_id: UUID | None = None) -> Sequence[Transaction]:
        query = select(Transaction).order_by(Transaction.created.desc())
        if user_id:
            query = query.where(Transaction.user_id == user_id)

        db_transactions = await self.session.scalars(query)
        return db_transactions.all()

    async def create_transaction(self, user_id: UUID, currency: CurrencyEnum, amount: Decimal) -> Transaction:
        new_transaction = Transaction(user_id=user_id, currency=currency, amount=amount)
        self.session.add(new_transaction)
        return new_transaction

    async def get_transaction_by_id(self, transaction_id: UUID) -> Transaction | None:
        query = select(Transaction).where(Transaction.id == transaction_id)
        result = await self.session.scalars(query)
        return result.one_or_none()
