from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select

from app.core.enums import CurrencyEnum, TransactionTypeEnum, UserStatusEnum
from app.models.balance import UserBalance
from app.models.transaction import Transaction
from tests.fixtures.users import user_for_api

prefix = "/api/v1"


class TestGetTransactionsAPI:
    async def test_get_transactions_returns_all(self, client, transaction_factory):
        await transaction_factory()
        await transaction_factory()

        response = await client.get(f"{prefix}/transactions")

        assert response.status_code == 200
        assert len(response.json()) == 2

    async def test_get_transactions_filters_by_user_id(self, client, transaction_factory):
        t1 = await transaction_factory()
        await transaction_factory()

        response = await client.get(f"{prefix}/transactions", params={"user_id": t1.user_id})

        assert response.status_code == 200

        data = response.json()
        assert len(data) == 1
        assert data[0]["user_id"] == str(t1.user_id)

    async def test_get_transactions_response_structure(self, client, transaction_factory):
        await transaction_factory()

        response = await client.get(f"{prefix}/transactions")
        assert response.status_code == 200
        transaction = response.json()[0]

        assert "id" in transaction
        assert "user_id" in transaction
        assert "currency" in transaction
        assert "amount" in transaction
        assert "operation_type" in transaction


class TestCreateTransactionAPI:
    async def test_create_transaction_success(self, client, user_factory, user_balance_factory, session):
        user = await user_factory()

        await user_balance_factory(
            user=user,
            currency=CurrencyEnum.USD,
            amount=Decimal("100.00"),
        )
        await session.commit()

        response = await client.post(
            f"{prefix}/{user.id}/transactions",
            json={"currency": CurrencyEnum.USD, "amount": "100.00", "operation_type": TransactionTypeEnum.DEPOSIT},
        )

        assert response.status_code == 201
        data = response.json()

        assert data["user_id"] == str(user.id)
        assert data["currency"] == CurrencyEnum.USD
        assert Decimal(data["amount"]) == Decimal("100.00")
        assert data["operation_type"] == TransactionTypeEnum.DEPOSIT

        balance = (await session.scalars(select(UserBalance).where(UserBalance.user_id == user.id))).one_or_none()

        assert balance is not None
        assert balance.amount == Decimal("200.00")

        transaction = (await session.scalars(select(Transaction).where(Transaction.id == data["id"]))).one_or_none()

        assert transaction is not None
        assert transaction.user_id == user.id

    async def test_create_transaction_reversal_not_allowed(self, client, user_for_api):
        user = await user_for_api()

        response = await client.post(
            f"{prefix}/{user.id}/transactions",
            json={"currency": CurrencyEnum.USD, "amount": "100.00", "operation_type": TransactionTypeEnum.REVERSAL},
        )

        assert response.status_code == 422
        assert "detail" in response.json()

    async def test_create_transaction_user_not_found(self, client):
        uuid = str(uuid4())

        response = await client.post(
            f"{prefix}/{uuid}/transactions",
            json={"currency": CurrencyEnum.USD, "amount": "100.00", "operation_type": TransactionTypeEnum.WITHDRAW},
        )

        assert response.status_code == 404
        assert response.json()["detail"] == f"User with id=`{uuid}` does not exist"

    async def test_create_transaction_blocked_user(self, client, user_for_api):
        user = await user_for_api(status=UserStatusEnum.BLOCKED)

        response = await client.post(
            f"{prefix}/{user.id}/transactions",
            json={"currency": CurrencyEnum.USD, "amount": "100.00", "operation_type": TransactionTypeEnum.WITHDRAW},
        )

        assert response.status_code == 400
        assert response.json()["detail"] == f"User with id=`{user.id}` is blocked"

    async def test_create_transaction_balance_not_found(self, client, user_for_api):
        user = await user_for_api()

        response = await client.post(
            f"{prefix}/{user.id}/transactions",
            json={"currency": CurrencyEnum.USD, "amount": "100.00", "operation_type": TransactionTypeEnum.WITHDRAW},
        )

        assert response.status_code == 404
        assert (
            response.json()["detail"] == f"Balance for user_id=`{user.id}` and currency=`{CurrencyEnum.USD}` not found"
        )

    async def test_create_transaction_negative_balance_after_operation(
        self, user_factory, session, user_balance_factory, client
    ):
        user = await user_factory()

        await user_balance_factory(
            user=user,
            currency=CurrencyEnum.USD,
            amount=Decimal("100.00"),
        )
        await session.commit()

        response = await client.post(
            f"{prefix}/{user.id}/transactions",
            json={"currency": CurrencyEnum.USD, "amount": "100.01", "operation_type": TransactionTypeEnum.WITHDRAW},
        )

        assert response.status_code == 400

    async def test_create_transaction_invalid_currency(self, client, user_for_api):
        user = await user_for_api()

        response = await client.post(
            f"{prefix}/{user.id}/transactions",
            json={"currency": "incorrect", "amount": "100.01", "operation_type": TransactionTypeEnum.WITHDRAW},
        )
        assert response.status_code == 422

    async def test_create_transaction_invalid_amount(self, client, user_for_api):
        user = await user_for_api()

        response = await client.post(
            f"{prefix}/{user.id}/transactions",
            json={"currency": CurrencyEnum.USD, "amount": "-1.00", "operation_type": TransactionTypeEnum.WITHDRAW},
        )
        assert response.status_code == 422


class TestRollbackTransactionAPI:
    async def test_rollback_transaction_deposit_success(
        self, client, user_factory, user_balance_factory, transaction_factory, session
    ):
        user = await user_factory()
        balance = await user_balance_factory(user=user, currency=CurrencyEnum.USD, amount=Decimal("100.00"))
        transaction = await transaction_factory(
            user=user,
            currency=CurrencyEnum.USD,
            amount=Decimal("30.00"),
            operation_type=TransactionTypeEnum.DEPOSIT,
        )

        await session.commit()

        response = await client.patch(f"{prefix}/{user.id}/transactions/{transaction.id}")

        assert response.status_code == 200
        data = response.json()

        assert data["user_id"] == str(user.id)
        assert data["currency"] == CurrencyEnum.USD
        assert Decimal(data["amount"]) == Decimal("30.00")
        assert data["operation_type"] == TransactionTypeEnum.REVERSAL

        await session.refresh(balance)
        assert balance.amount == Decimal("70.00")

        reversal = (
            await session.scalars(select(Transaction).where(Transaction.reversal_of_id == transaction.id))
        ).one()

        assert reversal.user_id == user.id
        assert reversal.currency == CurrencyEnum.USD
        assert reversal.amount == Decimal("30.00")
        assert reversal.operation_type == TransactionTypeEnum.REVERSAL

        original = (await session.scalars(select(Transaction).where(Transaction.id == transaction.id))).one()

        assert original.reversal_of_id is None
        assert reversal.reversal_of_id == original.id

    async def test_rollback_transaction_withdraw_success(
        self, client, user_factory, user_balance_factory, transaction_factory, session
    ):
        user = await user_factory()
        balance = await user_balance_factory(user=user, currency=CurrencyEnum.USD, amount=Decimal("50.00"))
        transaction = await transaction_factory(
            user=user,
            currency=CurrencyEnum.USD,
            amount=Decimal("30.00"),
            operation_type=TransactionTypeEnum.WITHDRAW,
        )

        await session.commit()

        response = await client.patch(f"{prefix}/{user.id}/transactions/{transaction.id}")

        assert response.status_code == 200
        data = response.json()

        assert data["user_id"] == str(user.id)
        assert data["currency"] == CurrencyEnum.USD
        assert Decimal(data["amount"]) == Decimal("30.00")
        assert data["operation_type"] == TransactionTypeEnum.REVERSAL

        await session.refresh(balance)
        assert balance.amount == Decimal("80.00")

        reversal = (
            await session.scalars(select(Transaction).where(Transaction.reversal_of_id == transaction.id))
        ).one()

        assert reversal.user_id == user.id
        assert reversal.currency == CurrencyEnum.USD
        assert reversal.amount == Decimal("30.00")
        assert reversal.operation_type == TransactionTypeEnum.REVERSAL

        original = (await session.scalars(select(Transaction).where(Transaction.id == transaction.id))).one()

        assert original.reversal_of_id is None
        assert reversal.reversal_of_id == original.id

    async def test_rollback_transaction_user_not_found(self, client, transaction_factory):
        transaction = await transaction_factory()

        response = await client.patch(f"{prefix}/{uuid4()}/transactions/{transaction.id}")

        assert response.status_code == 404
        assert "detail" in response.json()

    async def test_rollback_transaction_transaction_not_found(self, client, user_for_api):
        user = await user_for_api()

        response = await client.patch(f"{prefix}/{user.id}/transactions/{uuid4()}")

        assert response.status_code == 404
        assert "detail" in response.json()

    async def test_rollback_transaction_reversal_not_allowed(self, client, transaction_factory, session):
        reversal = await transaction_factory(operation_type=TransactionTypeEnum.REVERSAL)
        await session.commit()

        response = await client.patch(f"{prefix}/{reversal.user_id}/transactions/{reversal.id}")

        assert response.status_code == 400
        assert "detail" in response.json()

    async def test_rollback_transaction_of_another_user(self, client, user_factory, transaction_factory, session):
        user1 = await user_factory()
        user2 = await user_factory()
        transaction = await transaction_factory(user=user2)

        await session.commit()

        response = await client.patch(f"{prefix}/{user1.id}/transactions/{transaction.id}")

        assert response.status_code == 400
        assert "detail" in response.json()

    async def test_rollback_transaction_twice(
        self, client, session, user_factory, user_balance_factory, transaction_factory
    ):
        user = await user_factory()
        await user_balance_factory(
            user=user,
            currency=CurrencyEnum.USD,
            amount=Decimal("100"),
        )

        transaction = await transaction_factory(
            user=user,
            currency=CurrencyEnum.USD,
            amount=Decimal("20"),
        )

        await session.commit()

        response = await client.patch(f"{prefix}/{user.id}/transactions/{transaction.id}")
        assert response.status_code == 200

        response = await client.patch(f"{prefix}/{user.id}/transactions/{transaction.id}")
        assert response.status_code == 400

    async def test_rollback_transaction_user_blocked(self, client, user_factory, transaction_factory, session):
        user = await user_factory(status=UserStatusEnum.BLOCKED)
        transaction = await transaction_factory(user=user)

        await session.commit()

        response = await client.patch(f"{prefix}/{user.id}/transactions/{transaction.id}")
        assert response.status_code == 400

    async def test_rollback_transaction_balance_not_found(
        self, client, user_factory, user_balance_factory, transaction_factory, session
    ):
        user = await user_factory()
        await user_balance_factory(user=user, currency=CurrencyEnum.EUR, amount=Decimal("100"))
        transaction = await transaction_factory(
            user=user,
            currency=CurrencyEnum.USD,
            amount=Decimal("20"),
            operation_type=TransactionTypeEnum.DEPOSIT,
        )

        await session.commit()

        response = await client.patch(f"{prefix}/{user.id}/transactions/{transaction.id}")
        assert response.status_code == 404

    async def test_rollback_transaction_negative_balance(
        self, client, user_factory, user_balance_factory, transaction_factory, session
    ):
        user = await user_factory()
        await user_balance_factory(user=user, currency=CurrencyEnum.USD, amount=Decimal("50"))
        transaction = await transaction_factory(
            user=user,
            currency=CurrencyEnum.USD,
            amount=Decimal("51"),
            operation_type=TransactionTypeEnum.DEPOSIT,
        )

        await session.commit()

        response = await client.patch(f"{prefix}/{user.id}/transactions/{transaction.id}")

        assert response.status_code == 400
