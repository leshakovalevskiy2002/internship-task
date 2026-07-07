from decimal import Decimal
from typing import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import CurrencyEnum, TransactionStatusEnum, UserStatusEnum
from app.models.transaction import Transaction
from app.repositories.balances import BalanceRepository
from app.repositories.transactions import TransactionRepository
from app.repositories.users import UserRepository
from app.services.service_errors.transaction_errors import (
    NegativeBalanceError,
    TransactionAlreadyRollbackedException,
    TransactionBlockedUserException,
    TransactionDoesNotBelongToUserException,
    TransactionNotExistsError,
    TransactionUserBlockedError,
    TransactionUserNotFoundError,
    UserBalanceNotFoundError,
)


class TransactionService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.balance_repo = BalanceRepository(session)
        self.transaction_repo = TransactionRepository(session)

    async def get_all_transactions(self, user_id: UUID | None = None) -> Sequence[Transaction]:
        db_transactions = await self.transaction_repo.get_all_transactions(user_id=user_id)
        return db_transactions

    async def create_transaction(self, user_id: UUID, currency: CurrencyEnum, amount: Decimal) -> Transaction:
        db_user = await self.user_repo.get_user_by_id(user_id)
        if db_user is None:
            raise TransactionUserNotFoundError(user_id)

        if db_user.status != UserStatusEnum.ACTIVE:
            raise TransactionUserBlockedError(user_id)

        db_user_balance = await self.balance_repo.get_user_balance(user_id=user_id, currency=currency)
        if db_user_balance is None:
            raise UserBalanceNotFoundError(user_id=user_id, currency=currency.value)

        new_balance_amount = db_user_balance.amount + amount
        if new_balance_amount < 0:
            raise NegativeBalanceError(new_balance=new_balance_amount)

        await self.balance_repo.update_balance_amount(db_user_balance, new_balance_amount)
        new_transaction = await self.transaction_repo.create_transaction(
            user_id=user_id,
            currency=currency,
            amount=amount,
        )
        await self.session.commit()
        await self.session.refresh(new_transaction)
        return new_transaction

    async def rollback_transaction(self, transaction_id: UUID, user_id: UUID) -> Transaction:
        db_user = await self.user_repo.get_user_by_id(user_id)
        if db_user is None:
            raise TransactionUserNotFoundError(user_id)

        db_transaction = await self.transaction_repo.get_transaction_by_id(transaction_id)
        if db_transaction is None:
            raise TransactionNotExistsError(transaction_id)

        if db_transaction.user_id != db_user.id:
            raise TransactionDoesNotBelongToUserException(transaction_id=transaction_id, user_id=db_user.id)

        if db_transaction.status == TransactionStatusEnum.ROLL_BACKED:
            raise TransactionAlreadyRollbackedException(transaction_id=transaction_id)

        if db_user.status == UserStatusEnum.BLOCKED:
            raise TransactionBlockedUserException(user_id=user_id)

        db_user_balance = await self.balance_repo.get_user_balance(user_id=user_id, currency=db_transaction.currency)

        if db_user_balance is None:
            raise UserBalanceNotFoundError(user_id=user_id, currency=db_transaction.currency.value)

        user_balance_amount = db_user_balance.amount
        new_user_balance_amount = user_balance_amount - db_transaction.amount

        if new_user_balance_amount < 0:
            raise NegativeBalanceError(new_balance=new_user_balance_amount)

        await self.balance_repo.update_balance_amount(db_user_balance, new_user_balance_amount)
        roll_backed_transaction = await self.transaction_repo.roll_back_transaction(transaction=db_transaction)
        await self.session.commit()
        await self.session.refresh(roll_backed_transaction)
        return roll_backed_transaction
