from decimal import Decimal
from uuid import UUID

from app.core.enums import CurrencyEnum, TransactionStatusEnum, UserStatusEnum
from app.models.transaction import Transaction
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
from app.uow import UnitOfWork


class TransactionService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def create_transaction(self, user_id: UUID, currency: CurrencyEnum, amount: Decimal) -> Transaction:
        async with self.uow as uow:
            user = await uow.users.get_user_by_id(user_id)

            if user is None:
                raise TransactionUserNotFoundError(user_id)

            if user.status != UserStatusEnum.ACTIVE:
                raise TransactionUserBlockedError(user_id)

            user_balance = await uow.balances.get_user_balance_for_update(user_id=user_id, currency=currency)

            if user_balance is None:
                raise UserBalanceNotFoundError(user_id=user_id, currency=currency.value)

            new_balance_amount = user_balance.amount + amount

            if new_balance_amount < 0:
                raise NegativeBalanceError(new_balance=new_balance_amount)

            user_balance.amount = new_balance_amount

            new_transaction = await uow.transactions.create_transaction(
                user_id=user_id,
                currency=currency,
                amount=amount,
            )

            await uow.session.flush()
            await uow.session.refresh(new_transaction)

            return new_transaction

    async def rollback_transaction(self, transaction_id: UUID, user_id: UUID) -> Transaction:
        async with self.uow as uow:
            user = await uow.users.get_user_by_id(user_id)

            if user is None:
                raise TransactionUserNotFoundError(user_id)

            transaction = await uow.transactions.get_transaction_by_id_for_update(transaction_id)

            if transaction is None:
                raise TransactionNotExistsError(transaction_id)

            if transaction.user_id != user.id:
                raise TransactionDoesNotBelongToUserException(transaction_id=transaction_id, user_id=user.id)

            if transaction.status == TransactionStatusEnum.ROLL_BACKED:
                raise TransactionAlreadyRollbackedException(transaction_id=transaction_id)

            if user.status == UserStatusEnum.BLOCKED:
                raise TransactionBlockedUserException(user_id=user_id)

            user_balance = await uow.balances.get_user_balance_for_update(
                user_id=user_id, currency=transaction.currency
            )

            if user_balance is None:
                raise UserBalanceNotFoundError(user_id=user_id, currency=transaction.currency.value)

            user_balance_amount = user_balance.amount
            new_user_balance_amount = user_balance_amount - transaction.amount

            if new_user_balance_amount < 0:
                raise NegativeBalanceError(new_balance=new_user_balance_amount)

            user_balance.amount = new_user_balance_amount
            transaction.status = TransactionStatusEnum.ROLL_BACKED

            await uow.session.flush()
            await uow.session.refresh(transaction)
            return transaction
