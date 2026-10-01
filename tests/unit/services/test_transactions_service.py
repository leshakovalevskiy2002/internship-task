from decimal import Decimal
from uuid import uuid4

import pytest

from app.core.enums import CurrencyEnum, TransactionTypeEnum, UserStatusEnum
from app.models.balance import UserBalance
from app.models.transaction import Transaction
from app.models.user import User
from app.services.service_errors.transaction_errors import (
    NegativeBalanceError,
    TransactionAlreadyRollbackedException,
    TransactionBlockedUserException,
    TransactionDoesNotBelongToUserException,
    TransactionNotFoundError,
    TransactionReversalNotAllowedError,
    TransactionUserBlockedError,
    TransactionUserNotFoundError,
    UserBalanceNotFoundError,
)
from app.services.transactions_service import TransactionService


class TestTransactionService:
    class TestCreateTransaction:
        async def test_create_transaction_deposit_success(self, mocker):
            uow = mocker.AsyncMock()
            users = mocker.AsyncMock()
            balances = mocker.AsyncMock()
            transactions = mocker.AsyncMock()

            uow_context = uow.__aenter__.return_value
            uow_context.users = users
            uow_context.balances = balances
            uow_context.transactions = transactions

            user = User(email="test@example.com", status=UserStatusEnum.ACTIVE)
            balance = UserBalance(user_id=user.id, currency=CurrencyEnum.USD, amount=Decimal("100.00"))
            transaction = Transaction(
                user_id=user.id,
                currency=CurrencyEnum.USD,
                amount=Decimal("50.00"),
                operation_type=TransactionTypeEnum.DEPOSIT,
            )

            users.get_user_by_id.return_value = user
            balances.get_user_balance_for_update.return_value = balance
            transactions.create_transaction.return_value = transaction

            service = TransactionService(uow)

            result = await service.create_transaction(
                user_id=user.id,
                currency=CurrencyEnum.USD,
                amount=Decimal("50.00"),
                operation_type=TransactionTypeEnum.DEPOSIT,
            )

            assert result == transaction
            assert balance.amount == Decimal("150.00")

            users.get_user_by_id.assert_called_once_with(user.id)
            balances.get_user_balance_for_update.assert_called_once_with(user_id=user.id, currency=CurrencyEnum.USD)
            transactions.create_transaction.assert_called_once()
            uow_context.session.flush.assert_awaited_once()
            uow_context.session.refresh.assert_awaited_once_with(transaction)

        async def test_create_transaction_withdraw_success(self, mocker):
            uow = mocker.AsyncMock()
            users = mocker.AsyncMock()
            balances = mocker.AsyncMock()
            transactions = mocker.AsyncMock()

            uow_context = uow.__aenter__.return_value
            uow_context.users = users
            uow_context.balances = balances
            uow_context.transactions = transactions

            user = User(email="test@example.com", status=UserStatusEnum.ACTIVE)
            balance = UserBalance(user_id=user.id, currency=CurrencyEnum.USD, amount=Decimal("100.00"))
            transaction = Transaction(
                user_id=user.id,
                currency=CurrencyEnum.USD,
                amount=Decimal("60.00"),
                operation_type=TransactionTypeEnum.WITHDRAW,
            )

            users.get_user_by_id.return_value = user
            balances.get_user_balance_for_update.return_value = balance
            transactions.create_transaction.return_value = transaction

            service = TransactionService(uow)

            result = await service.create_transaction(
                user_id=user.id,
                currency=CurrencyEnum.USD,
                amount=Decimal("60.00"),
                operation_type=TransactionTypeEnum.WITHDRAW,
            )

            assert result == transaction
            assert balance.amount == Decimal("40.00")

            users.get_user_by_id.assert_called_once_with(user.id)
            balances.get_user_balance_for_update.assert_called_once_with(user_id=user.id, currency=CurrencyEnum.USD)
            transactions.create_transaction.assert_called_once()
            uow_context.session.flush.assert_awaited_once()
            uow_context.session.refresh.assert_awaited_once_with(transaction)

        async def test_create_transaction_reversal_not_allowed(self, mocker):
            uow = mocker.AsyncMock()

            service = TransactionService(uow)

            with pytest.raises(TransactionReversalNotAllowedError):
                await service.create_transaction(
                    user_id=uuid4(),
                    currency=CurrencyEnum.USD,
                    amount=Decimal("50.00"),
                    operation_type=TransactionTypeEnum.REVERSAL,
                )

        async def test_create_transaction_user_not_found(self, mocker):
            uow = mocker.AsyncMock()
            users = mocker.AsyncMock()

            uow_context = uow.__aenter__.return_value
            uow_context.users = users

            users.get_user_by_id.return_value = None

            service = TransactionService(uow)

            with pytest.raises(TransactionUserNotFoundError):
                await service.create_transaction(
                    user_id=uuid4(),
                    currency=CurrencyEnum.USD,
                    amount=Decimal("50.00"),
                    operation_type=TransactionTypeEnum.DEPOSIT,
                )

        async def test_create_transaction_user_blocked(self, mocker):
            uow = mocker.AsyncMock()
            users = mocker.AsyncMock()

            uow_context = uow.__aenter__.return_value
            uow_context.users = users

            user = User(email="test@example.com", status=UserStatusEnum.BLOCKED)
            users.get_user_by_id.return_value = user

            service = TransactionService(uow)

            with pytest.raises(TransactionUserBlockedError):
                await service.create_transaction(
                    user_id=user.id,
                    currency=CurrencyEnum.USD,
                    amount=Decimal("50.00"),
                    operation_type=TransactionTypeEnum.WITHDRAW,
                )

        async def test_create_transaction_balance_not_found(self, mocker):
            uow = mocker.AsyncMock()
            users = mocker.AsyncMock()
            balances = mocker.AsyncMock()

            uow_context = uow.__aenter__.return_value
            uow_context.users = users
            uow_context.balances = balances

            user = User(email="test@example.com", status=UserStatusEnum.ACTIVE)

            users.get_user_by_id.return_value = user
            balances.get_user_balance_for_update.return_value = None

            service = TransactionService(uow)

            with pytest.raises(UserBalanceNotFoundError):
                await service.create_transaction(
                    user_id=user.id,
                    currency=CurrencyEnum.USD,
                    amount=Decimal("100.00"),
                    operation_type=TransactionTypeEnum.DEPOSIT,
                )

        async def test_create_transaction_negative_balance(self, mocker):
            uow = mocker.AsyncMock()
            users = mocker.AsyncMock()
            balances = mocker.AsyncMock()
            transactions = mocker.AsyncMock()

            uow_context = uow.__aenter__.return_value
            uow_context.users = users
            uow_context.balances = balances
            uow_context.transactions = transactions

            user = User(email="test@example.com", status=UserStatusEnum.ACTIVE)
            balance = UserBalance(user_id=user.id, currency=CurrencyEnum.USD, amount=Decimal("50.00"))

            users.get_user_by_id.return_value = user
            balances.get_user_balance_for_update.return_value = balance

            service = TransactionService(uow)

            with pytest.raises(NegativeBalanceError):
                await service.create_transaction(
                    user_id=user.id,
                    currency=CurrencyEnum.USD,
                    amount=Decimal("60.00"),
                    operation_type=TransactionTypeEnum.WITHDRAW,
                )
            assert balance.amount == Decimal("50.00")
            transactions.create_transaction.assert_not_called()
            uow_context.session.flush.assert_not_awaited()

        async def test_create_transaction_withdraw_zero_balance(self, mocker):
            uow = mocker.AsyncMock()
            users = mocker.AsyncMock()
            balances = mocker.AsyncMock()
            transactions = mocker.AsyncMock()

            uow_context = uow.__aenter__.return_value
            uow_context.users = users
            uow_context.balances = balances
            uow_context.transactions = transactions

            user = User(email="test@example.com", status=UserStatusEnum.ACTIVE)
            balance = UserBalance(user_id=user.id, currency=CurrencyEnum.USD, amount=Decimal("50.00"))

            users.get_user_by_id.return_value = user
            balances.get_user_balance_for_update.return_value = balance

            service = TransactionService(uow)
            await service.create_transaction(
                user_id=user.id,
                currency=CurrencyEnum.USD,
                amount=Decimal("50.00"),
                operation_type=TransactionTypeEnum.WITHDRAW,
            )

            assert balance.amount == Decimal("0.00")
            transactions.create_transaction.assert_called_once()
            uow_context.session.flush.assert_called_once()

    class TestRollbackTransaction:
        async def test_rollback_deposit_success(self, mocker):
            uow = mocker.AsyncMock()
            users = mocker.AsyncMock()
            balances = mocker.AsyncMock()
            transactions = mocker.AsyncMock()

            uow_context = uow.__aenter__.return_value
            uow_context.users = users
            uow_context.balances = balances
            uow_context.transactions = transactions

            user = User(email="test@example.com", status=UserStatusEnum.ACTIVE)
            transaction = Transaction(
                user_id=user.id,
                currency=CurrencyEnum.USD,
                amount=Decimal("100.00"),
                operation_type=TransactionTypeEnum.DEPOSIT,
            )
            balance = UserBalance(user_id=user.id, currency=CurrencyEnum.USD, amount=Decimal("150.00"))
            reversal_transaction = Transaction(
                user_id=user.id,
                currency=CurrencyEnum.USD,
                amount=Decimal("100.00"),
                operation_type=TransactionTypeEnum.REVERSAL,
            )

            users.get_user_by_id.return_value = user
            transactions.get_transaction_by_id_for_update.return_value = transaction
            balances.get_user_balance_for_update.return_value = balance
            transactions.create_transaction.return_value = reversal_transaction

            service = TransactionService(uow)

            result = await service.rollback_transaction(transaction.id, user.id)

            assert result == reversal_transaction
            assert balance.amount == Decimal("50.00")
            assert transaction.reversal == reversal_transaction

            transactions.create_transaction.assert_called_once_with(
                user_id=user.id,
                currency=CurrencyEnum.USD,
                amount=Decimal("100.00"),
                operation_type=TransactionTypeEnum.REVERSAL,
            )

            uow_context.session.flush.assert_called_once()
            uow_context.session.refresh.assert_called_once_with(reversal_transaction)

        async def test_rollback_withdraw_success(self, mocker):
            uow = mocker.AsyncMock()
            users = mocker.AsyncMock()
            balances = mocker.AsyncMock()
            transactions = mocker.AsyncMock()

            uow_context = uow.__aenter__.return_value
            uow_context.users = users
            uow_context.balances = balances
            uow_context.transactions = transactions

            user = User(email="test@example.com", status=UserStatusEnum.ACTIVE)
            transaction = Transaction(
                user_id=user.id,
                currency=CurrencyEnum.USD,
                amount=Decimal("100.00"),
                operation_type=TransactionTypeEnum.WITHDRAW,
            )
            balance = UserBalance(user_id=user.id, currency=CurrencyEnum.USD, amount=Decimal("50.00"))
            reversal_transaction = Transaction(
                user_id=user.id,
                currency=CurrencyEnum.USD,
                amount=Decimal("100.00"),
                operation_type=TransactionTypeEnum.REVERSAL,
            )

            users.get_user_by_id.return_value = user
            transactions.get_transaction_by_id_for_update.return_value = transaction
            balances.get_user_balance_for_update.return_value = balance
            transactions.create_transaction.return_value = reversal_transaction

            service = TransactionService(uow)

            result = await service.rollback_transaction(transaction.id, user.id)

            assert result == reversal_transaction
            assert balance.amount == Decimal("150.00")
            assert transaction.reversal == reversal_transaction

            transactions.create_transaction.assert_called_once_with(
                user_id=user.id,
                currency=CurrencyEnum.USD,
                amount=Decimal("100.00"),
                operation_type=TransactionTypeEnum.REVERSAL,
            )

            uow_context.session.flush.assert_called_once()
            uow_context.session.refresh.assert_called_once_with(reversal_transaction)

        async def test_rollback_user_not_found(self, mocker):
            uow = mocker.AsyncMock()
            users = mocker.AsyncMock()

            uow_context = uow.__aenter__.return_value
            uow_context.users = users

            users.get_user_by_id.return_value = None

            service = TransactionService(uow)

            with pytest.raises(TransactionUserNotFoundError):
                await service.rollback_transaction(uuid4(), uuid4())

        async def test_rollback_transaction_not_found(self, mocker):
            uow = mocker.AsyncMock()
            users = mocker.AsyncMock()
            transactions = mocker.AsyncMock()

            uow_context = uow.__aenter__.return_value
            uow_context.users = users
            uow_context.transactions = transactions

            user = User(email="test@example.com", status=UserStatusEnum.ACTIVE)

            users.get_user_by_id.return_value = user
            transactions.get_transaction_by_id_for_update.return_value = None

            service = TransactionService(uow)

            with pytest.raises(TransactionNotFoundError):
                await service.rollback_transaction(uuid4(), user.id)

        async def test_rollback_reversal_transaction_not_allowed(self, mocker):
            uow = mocker.AsyncMock()
            users = mocker.AsyncMock()
            transactions = mocker.AsyncMock()

            uow_context = uow.__aenter__.return_value
            uow_context.users = users
            uow_context.transactions = transactions

            user = User(email="test@example.com", status=UserStatusEnum.ACTIVE)
            transaction = Transaction(
                user_id=user.id,
                currency=CurrencyEnum.USD,
                amount=Decimal("10"),
                operation_type=TransactionTypeEnum.REVERSAL,
            )

            users.get_user_by_id.return_value = user
            transactions.get_transaction_by_id_for_update.return_value = transaction

            service = TransactionService(uow)

            with pytest.raises(TransactionReversalNotAllowedError):
                await service.rollback_transaction(transaction.id, user.id)

        async def test_rollback_transaction_belongs_to_another_user(self, mocker):
            uow = mocker.AsyncMock()
            users = mocker.AsyncMock()
            transactions = mocker.AsyncMock()

            uow_context = uow.__aenter__.return_value
            uow_context.users = users
            uow_context.transactions = transactions

            user = User(email="test@example.com", status=UserStatusEnum.ACTIVE)
            transaction = Transaction(
                user_id=uuid4(),
                currency=CurrencyEnum.USD,
                amount=Decimal("10"),
                operation_type=TransactionTypeEnum.DEPOSIT,
            )

            users.get_user_by_id.return_value = user
            transactions.get_transaction_by_id_for_update.return_value = transaction

            service = TransactionService(uow)

            with pytest.raises(TransactionDoesNotBelongToUserException):
                await service.rollback_transaction(transaction.id, user.id)

        async def test_rollback_transaction_already_roll_backed(self, mocker):
            uow = mocker.AsyncMock()
            users = mocker.AsyncMock()
            transactions = mocker.AsyncMock()

            uow_context = uow.__aenter__.return_value
            uow_context.users = users
            uow_context.transactions = transactions

            user = User(email="test@example.com", status=UserStatusEnum.ACTIVE)
            transaction = Transaction(
                user_id=user.id,
                currency=CurrencyEnum.USD,
                amount=Decimal("10"),
                operation_type=TransactionTypeEnum.DEPOSIT,
            )
            reversal = Transaction(
                user_id=user.id,
                currency=CurrencyEnum.USD,
                amount=Decimal("10"),
                operation_type=TransactionTypeEnum.REVERSAL,
            )

            transaction.reversal = reversal

            users.get_user_by_id.return_value = user
            transactions.get_transaction_by_id_for_update.return_value = transaction

            service = TransactionService(uow)

            with pytest.raises(TransactionAlreadyRollbackedException):
                await service.rollback_transaction(transaction.id, user.id)

        async def test_rollback_blocked_user(self, mocker):
            uow = mocker.AsyncMock()
            users = mocker.AsyncMock()
            transactions = mocker.AsyncMock()

            uow_context = uow.__aenter__.return_value
            uow_context.users = users
            uow_context.transactions = transactions

            user = User(email="test@example.com", status=UserStatusEnum.BLOCKED)
            transaction = Transaction(
                user_id=user.id,
                currency=CurrencyEnum.USD,
                amount=Decimal("10"),
                operation_type=TransactionTypeEnum.DEPOSIT,
            )

            users.get_user_by_id.return_value = user
            transactions.get_transaction_by_id_for_update.return_value = transaction

            service = TransactionService(uow)

            with pytest.raises(TransactionBlockedUserException):
                await service.rollback_transaction(transaction.id, user.id)

        async def test_rollback_balance_not_found(self, mocker):
            uow = mocker.AsyncMock()
            users = mocker.AsyncMock()
            balances = mocker.AsyncMock()
            transactions = mocker.AsyncMock()

            uow_context = uow.__aenter__.return_value
            uow_context.users = users
            uow_context.transactions = transactions
            uow_context.balances = balances

            user = User(email="test@test.com", status=UserStatusEnum.ACTIVE)
            transaction = Transaction(
                user_id=user.id,
                currency=CurrencyEnum.USD,
                amount=Decimal("10"),
                operation_type=TransactionTypeEnum.DEPOSIT,
            )

            users.get_user_by_id.return_value = user
            transactions.get_transaction_by_id_for_update.return_value = transaction
            balances.get_user_balance_for_update.return_value = None

            service = TransactionService(uow)

            with pytest.raises(UserBalanceNotFoundError):
                await service.rollback_transaction(transaction.id, user.id)

        async def test_rollback_negative_balance(self, mocker):
            uow = mocker.AsyncMock()
            users = mocker.AsyncMock()
            balances = mocker.AsyncMock()
            transactions = mocker.AsyncMock()

            uow_context = uow.__aenter__.return_value
            uow_context.users = users
            uow_context.transactions = transactions
            uow_context.balances = balances

            user = User(email="test@test.com", status=UserStatusEnum.ACTIVE)
            transaction = Transaction(
                user_id=user.id,
                currency=CurrencyEnum.USD,
                amount=Decimal("100"),
                operation_type=TransactionTypeEnum.DEPOSIT,
            )
            balance = UserBalance(user_id=user.id, currency=CurrencyEnum.USD, amount=Decimal("50"))

            users.get_user_by_id.return_value = user
            transactions.get_transaction_by_id_for_update.return_value = transaction
            balances.get_user_balance_for_update.return_value = balance

            service = TransactionService(uow)

            with pytest.raises(NegativeBalanceError):
                await service.rollback_transaction(transaction.id, user.id)

            assert balance.amount == Decimal("50")
            transactions.create_transaction.assert_not_called()
            uow_context.session.flush.assert_not_awaited()

        async def test_rollback_deposit_zero_balance(self, mocker):
            uow = mocker.AsyncMock()
            users = mocker.AsyncMock()
            balances = mocker.AsyncMock()
            transactions = mocker.AsyncMock()

            uow_context = uow.__aenter__.return_value
            uow_context.users = users
            uow_context.transactions = transactions
            uow_context.balances = balances

            user = User(email="test@test.com", status=UserStatusEnum.ACTIVE)
            transaction = Transaction(
                user_id=user.id,
                currency=CurrencyEnum.USD,
                amount=Decimal("50.00"),
                operation_type=TransactionTypeEnum.DEPOSIT,
            )
            reversal_transaction = Transaction(
                user_id=user.id,
                currency=CurrencyEnum.USD,
                amount=Decimal("50.00"),
                operation_type=TransactionTypeEnum.REVERSAL,
            )
            balance = UserBalance(user_id=user.id, currency=CurrencyEnum.USD, amount=Decimal("50.00"))

            users.get_user_by_id.return_value = user
            transactions.get_transaction_by_id_for_update.return_value = transaction
            transactions.create_transaction.return_value = reversal_transaction
            balances.get_user_balance_for_update.return_value = balance

            service = TransactionService(uow)
            result = await service.rollback_transaction(transaction.id, user.id)

            assert balance.amount == Decimal("0.00")
            assert result == reversal_transaction
            uow_context.session.flush.assert_awaited_once()
            uow_context.session.refresh.assert_awaited_once_with(reversal_transaction)
