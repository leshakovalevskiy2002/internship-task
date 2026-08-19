from datetime import date, datetime, timezone
from decimal import Decimal

from app.core.constants import EXCHANGE_RATES_TO_USD
from app.core.enums import CurrencyEnum, TransactionTypeEnum


class TestReportRepository:
    UTC = timezone.utc

    async def test_get_registered_users_by_week(self, report_repository, user_factory):
        await user_factory(created=datetime(2026, 8, 3, 10, 0, tzinfo=self.UTC))
        await user_factory(created=datetime(2026, 8, 4, 15, 0, tzinfo=self.UTC))
        await user_factory(created=datetime(2026, 8, 10, 12, 0, tzinfo=self.UTC))

        result = await report_repository.get_registered_users_by_week(date(2026, 8, 1), date(2026, 8, 17))

        assert result == {date(2026, 8, 3): 2, date(2026, 8, 10): 1}

    async def test_get_registered_users_by_week_respects_date_range(self, report_repository, user_factory):
        await user_factory(created=datetime(2026, 8, 1, 0, 0, tzinfo=self.UTC))
        await user_factory(created=datetime(2026, 8, 16, 23, 59, tzinfo=self.UTC))
        await user_factory(created=datetime(2026, 8, 17, 0, 0, tzinfo=self.UTC))

        result = await report_repository.get_registered_users_by_week(
            date(2026, 8, 1),
            date(2026, 8, 17),
        )

        assert result == {date(2026, 7, 27): 1, date(2026, 8, 10): 1}

    async def test_get_deposit_users_by_week(self, report_repository, user_factory, transaction_factory):
        user_1 = await user_factory()
        user_2 = await user_factory()

        await transaction_factory(
            user=user_1,
            operation_type=TransactionTypeEnum.DEPOSIT,
            created=datetime(2026, 8, 3, 10, 0, tzinfo=self.UTC),
        )

        await transaction_factory(
            user=user_1,
            operation_type=TransactionTypeEnum.DEPOSIT,
            created=datetime(2026, 8, 4, 10, 0, tzinfo=self.UTC),
        )

        await transaction_factory(
            user=user_2,
            operation_type=TransactionTypeEnum.DEPOSIT,
            created=datetime(2026, 8, 10, 10, 0, tzinfo=self.UTC),
        )

        await transaction_factory(
            user=user_2,
            operation_type=TransactionTypeEnum.WITHDRAW,
            created=datetime(2026, 8, 10, 12, 0, tzinfo=self.UTC),
        )

        result = await report_repository.get_deposit_users_by_week(
            date(2026, 8, 1),
            date(2026, 8, 17),
        )

        assert result == {date(2026, 8, 3): 1, date(2026, 8, 10): 1}

    async def test_get_not_roll_backed_deposit_amount_by_week(
        self, report_repository, user_factory, transaction_factory
    ):
        user = await user_factory()

        await transaction_factory(
            user=user,
            operation_type=TransactionTypeEnum.DEPOSIT,
            amount=Decimal("100.00"),
            currency="USD",
            created=datetime(2026, 8, 3, 10, 0, tzinfo=self.UTC),
        )

        await transaction_factory(
            user=user,
            operation_type=TransactionTypeEnum.DEPOSIT,
            amount=Decimal("200.56"),
            currency="USD",
            created=datetime(2026, 8, 4, 10, 0, tzinfo=self.UTC),
        )

        result = await report_repository.get_not_roll_backed_deposit_amount_by_week(
            date(2026, 8, 1),
            date(2026, 8, 17),
        )

        assert result == {date(2026, 8, 3): Decimal("300.56")}

    async def test_get_not_roll_backed_deposit_amount_excludes_reversed_transaction(
        self, report_repository, user_factory, transaction_factory
    ):
        user = await user_factory()

        deposit = await transaction_factory(
            user=user,
            operation_type=TransactionTypeEnum.DEPOSIT,
            amount=Decimal("100.00"),
            currency="USD",
            created=datetime(2026, 8, 3, 10, 0, tzinfo=self.UTC),
        )

        await transaction_factory(
            user=user,
            operation_type=TransactionTypeEnum.DEPOSIT,
            amount=Decimal("200.56"),
            currency="USD",
            created=datetime(2026, 8, 4, 10, 0, tzinfo=self.UTC),
        )

        await transaction_factory(
            user=user,
            operation_type=TransactionTypeEnum.REVERSAL,
            reversal_of_id=deposit.id,
            amount=Decimal("100.00"),
            currency="USD",
            created=datetime(2026, 8, 5, 10, 0, tzinfo=self.UTC),
        )

        result = await report_repository.get_not_roll_backed_deposit_amount_by_week(
            date(2026, 8, 1),
            date(2026, 8, 17),
        )

        assert result == {date(2026, 8, 3): Decimal("200.56")}

    async def test_get_not_roll_backed_deposit_amount_applies_exchange_rate(
        self, report_repository, user_factory, transaction_factory
    ):
        user = await user_factory()

        await transaction_factory(
            user=user,
            operation_type=TransactionTypeEnum.DEPOSIT,
            amount=Decimal("100.00"),
            currency="USD",
            created=datetime(2026, 8, 3, 10, 0, tzinfo=self.UTC),
        )

        await transaction_factory(
            user=user,
            operation_type=TransactionTypeEnum.DEPOSIT,
            amount=Decimal("100.00"),
            currency="EUR",
            created=datetime(2026, 8, 4, 10, 0, tzinfo=self.UTC),
        )

        eur_rate = EXCHANGE_RATES_TO_USD[CurrencyEnum.EUR]

        result = await report_repository.get_not_roll_backed_deposit_amount_by_week(
            date(2026, 8, 1),
            date(2026, 8, 17),
        )

        assert result == {date(2026, 8, 3): Decimal("100.00") + Decimal("100.00") * eur_rate}

    async def test_get_not_roll_backed_withdraw_amount_by_week(
        self, report_repository, user_factory, transaction_factory
    ):
        user = await user_factory()

        await transaction_factory(
            user=user,
            operation_type=TransactionTypeEnum.WITHDRAW,
            amount=Decimal("100.00"),
            currency="USD",
            created=datetime(2026, 8, 3, 10, 0, tzinfo=self.UTC),
        )

        await transaction_factory(
            user=user,
            operation_type=TransactionTypeEnum.WITHDRAW,
            amount=Decimal("250.00"),
            currency="USD",
            created=datetime(2026, 8, 4, 10, 0, tzinfo=self.UTC),
        )

        result = await report_repository.get_not_roll_backed_withdraw_amount_by_week(
            date(2026, 8, 1),
            date(2026, 8, 17),
        )

        assert result == {date(2026, 8, 3): Decimal("350.00")}

    async def test_get_not_roll_backed_withdraw_amount_excludes_reversed_transaction(
        self, report_repository, user_factory, transaction_factory
    ):
        user = await user_factory()

        withdraw = await transaction_factory(
            user=user,
            operation_type=TransactionTypeEnum.WITHDRAW,
            amount=Decimal("100.00"),
            currency="USD",
            created=datetime(2026, 8, 3, 10, 0, tzinfo=self.UTC),
        )

        await transaction_factory(
            user=user,
            operation_type=TransactionTypeEnum.WITHDRAW,
            amount=Decimal("200.00"),
            currency="USD",
            created=datetime(2026, 8, 4, 10, 0, tzinfo=self.UTC),
        )

        await transaction_factory(
            user=user,
            operation_type=TransactionTypeEnum.REVERSAL,
            reversal_of_id=withdraw.id,
            amount=Decimal("100.00"),
            currency="USD",
            created=datetime(2026, 8, 5, 10, 0, tzinfo=self.UTC),
        )

        result = await report_repository.get_not_roll_backed_withdraw_amount_by_week(
            date(2026, 8, 1),
            date(2026, 8, 17),
        )

        assert result == {date(2026, 8, 3): Decimal("200.00")}

    async def test_get_transactions_count_by_week(self, report_repository, user_factory, transaction_factory):
        user = await user_factory()

        transaction = await transaction_factory(
            user=user,
            operation_type=TransactionTypeEnum.DEPOSIT,
            amount=Decimal("100.00"),
            currency="USD",
            created=datetime(2026, 8, 3, 10, 0, tzinfo=self.UTC),
        )

        await transaction_factory(
            user=user,
            operation_type=TransactionTypeEnum.WITHDRAW,
            amount=Decimal("50.00"),
            currency="USD",
            created=datetime(2026, 8, 4, 10, 0, tzinfo=self.UTC),
        )

        await transaction_factory(
            user=user,
            operation_type=TransactionTypeEnum.REVERSAL,
            reversal_of_id=transaction.id,
            amount=Decimal("100.00"),
            currency="USD",
            created=datetime(2026, 8, 5, 10, 0, tzinfo=self.UTC),
        )

        result = await report_repository.get_transactions_count_by_week(
            date(2026, 8, 1),
            date(2026, 8, 17),
        )

        assert result == {date(2026, 8, 3): 2}

    async def test_get_not_roll_backed_transactions_count_by_week(
        self, report_repository, user_factory, transaction_factory
    ):
        user = await user_factory()

        deposit = await transaction_factory(
            user=user,
            operation_type=TransactionTypeEnum.DEPOSIT,
            amount=Decimal("100.00"),
            currency="USD",
            created=datetime(2026, 8, 3, 10, 0, tzinfo=self.UTC),
        )

        await transaction_factory(
            user=user,
            operation_type=TransactionTypeEnum.DEPOSIT,
            amount=Decimal("200.00"),
            currency="USD",
            created=datetime(2026, 8, 4, 10, 0, tzinfo=self.UTC),
        )

        await transaction_factory(
            user=user,
            operation_type=TransactionTypeEnum.REVERSAL,
            reversal_of_id=deposit.id,
            amount=Decimal("100.00"),
            currency="USD",
            created=datetime(2026, 8, 5, 10, 0, tzinfo=self.UTC),
        )

        result = await report_repository.get_not_roll_backed_transactions_count_by_week(
            date(2026, 8, 1),
            date(2026, 8, 17),
        )

        assert result == {date(2026, 8, 3): 1}
