from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select

from app.core.enums import CurrencyEnum, TransactionTypeEnum
from app.models.transaction import Transaction


class TestTransactionRepository:
    async def test_get_transactions_returns_all(self, transaction_repository, transaction_factory):
        transaction1 = await transaction_factory()
        transaction2 = await transaction_factory()

        transactions = await transaction_repository.get_transactions()

        assert len(transactions) == 2
        assert {t.id for t in transactions} == {transaction1.id, transaction2.id}

    async def test_get_transactions_filters_by_user_id(self, user_factory, transaction_repository, transaction_factory):
        user1 = await user_factory()
        user2 = await user_factory()

        transaction1 = await transaction_factory(user=user1)
        transaction2 = await transaction_factory(user=user2)

        transactions = await transaction_repository.get_transactions(user_id=user1.id)

        assert len(transactions) == 1
        assert transactions[0].id == transaction1.id
        assert transactions[0].user_id == user1.id
        assert transactions[0].id != transaction2.id

    async def test_get_transactions_ordered_by_created_desc(self, transaction_repository, transaction_factory):
        old_transaction = await transaction_factory(created=datetime(2025, 1, 1))
        new_transaction = await transaction_factory(created=datetime(2025, 1, 2))

        transactions = await transaction_repository.get_transactions()

        assert transactions[0].id == new_transaction.id
        assert transactions[1].id == old_transaction.id

    async def test_create_transaction(self, transaction_repository, user_factory):
        session = transaction_repository.session

        user = await user_factory()
        transaction = await transaction_repository.create_transaction(
            user_id=user.id, amount=Decimal(100), operation_type=TransactionTypeEnum.DEPOSIT, currency=CurrencyEnum.CAD
        )
        await session.flush()

        db_transaction = (
            await session.scalars(select(Transaction).where(Transaction.id == transaction.id))
        ).one_or_none()

        assert db_transaction is not None
        assert db_transaction.user_id == user.id
        assert db_transaction.operation_type == TransactionTypeEnum.DEPOSIT
        assert db_transaction.currency == CurrencyEnum.CAD
        assert db_transaction.amount == Decimal(100)

    async def test_get_transaction_by_id(self, transaction_repository, transaction_factory):
        transaction = await transaction_factory()

        db_transaction = await transaction_repository.get_transaction_by_id_for_update(transaction_id=transaction.id)

        assert db_transaction is not None
        assert db_transaction.user_id == transaction.user_id
        assert db_transaction.amount == transaction.amount

    async def test_get_transaction_by_id_returns_none_when_not_found(self, transaction_repository):
        transaction = await transaction_repository.get_transaction_by_id_for_update(uuid4())
        assert transaction is None
