from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, cast, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import TransactionTypeEnum
from app.models.transaction import Transaction
from app.models.user import User
from app.queries.transaction_expressions import get_exchange_rate_case, has_reversal_transaction


@dataclass
class WeeklyStatistics:
    registered_users: dict[date, int]
    deposit_users: dict[date, int]
    deposit_amount: dict[date, Decimal]
    withdraw_amount: dict[date, Decimal]
    transactions: dict[date, int]
    not_roll_backed_transactions: dict[date, int]


class ReportRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_weekly_statistics(self, start_date: date, end_date: date) -> WeeklyStatistics:
        registered_users = await self.get_registered_users_by_week(start_date, end_date)
        deposit_users = await self.get_deposit_users_by_week(start_date, end_date)
        deposit_amount = await self.get_not_roll_backed_deposit_amount_by_week(start_date, end_date)
        withdraw_amount = await self.get_not_roll_backed_withdraw_amount_by_week(start_date, end_date)
        transactions = await self.get_transactions_count_by_week(start_date, end_date)
        not_roll_backed_transactions = await self.get_not_roll_backed_transactions_count_by_week(start_date, end_date)

        return WeeklyStatistics(
            registered_users=registered_users,
            deposit_users=deposit_users,
            deposit_amount=deposit_amount,
            withdraw_amount=withdraw_amount,
            transactions=transactions,
            not_roll_backed_transactions=not_roll_backed_transactions,
        )

    async def get_registered_users_by_week(self, start_date: date, end_date: date) -> dict[date, int]:
        query = (
            select(
                cast(func.date_trunc("week", User.created), Date).label("week"), func.count(User.id).label("user_count")
            )
            .where(User.created >= start_date, User.created < end_date)
            .group_by("week")
        )

        result = await self.session.execute(query)
        return {row.week: row.user_count for row in result}

    async def get_deposit_users_by_week(self, start_date: date, end_date: date) -> dict[date, int]:
        query = (
            select(
                cast(func.date_trunc("week", Transaction.created), Date).label("week"),
                func.count(distinct(User.id)).label("user_count"),
            )
            .join(Transaction, User.id == Transaction.user_id)
            .where(
                Transaction.created >= start_date,
                Transaction.created < end_date,
                Transaction.operation_type == TransactionTypeEnum.DEPOSIT,
            )
            .group_by("week")
        )

        result = await self.session.execute(query)
        return {row.week: row.user_count for row in result}

    async def get_not_roll_backed_deposit_amount_by_week(self, start_date: date, end_date: date) -> dict[date, Decimal]:
        query = (
            select(
                cast(func.date_trunc("week", Transaction.created), Date).label("week"),
                func.coalesce(func.sum(Transaction.amount * get_exchange_rate_case()), Decimal("0.00")).label(
                    "total_amount"
                ),
            )
            .where(
                Transaction.created >= start_date,
                Transaction.created < end_date,
                Transaction.operation_type == TransactionTypeEnum.DEPOSIT,
                ~has_reversal_transaction(),
            )
            .group_by("week")
        )

        result = await self.session.execute(query)
        return {row.week: row.total_amount for row in result}

    async def get_not_roll_backed_withdraw_amount_by_week(
        self, start_date: date, end_date: date
    ) -> dict[date, Decimal]:
        query = (
            select(
                cast(func.date_trunc("week", Transaction.created), Date).label("week"),
                func.coalesce(func.sum(Transaction.amount * get_exchange_rate_case()), Decimal("0.00")).label(
                    "total_amount"
                ),
            )
            .where(
                Transaction.created >= start_date,
                Transaction.created < end_date,
                Transaction.operation_type == TransactionTypeEnum.WITHDRAW,
                ~has_reversal_transaction(),
            )
            .group_by("week")
        )

        result = await self.session.execute(query)
        return {row.week: row.total_amount for row in result}

    async def get_transactions_count_by_week(self, start_date: date, end_date: date) -> dict[date, int]:
        query = (
            select(
                cast(func.date_trunc("week", Transaction.created), Date).label("week"),
                func.count(Transaction.id).label("transactions_count"),
            )
            .where(
                Transaction.created >= start_date,
                Transaction.created < end_date,
                Transaction.operation_type != TransactionTypeEnum.REVERSAL,
            )
            .group_by("week")
        )

        result = await self.session.execute(query)
        return {row.week: row.transactions_count for row in result}

    async def get_not_roll_backed_transactions_count_by_week(self, start_date: date, end_date: date) -> dict[date, int]:
        query = (
            select(
                cast(func.date_trunc("week", Transaction.created), Date).label("week"),
                func.count(Transaction.id).label("transactions_count"),
            )
            .where(
                Transaction.created >= start_date,
                Transaction.created < end_date,
                Transaction.operation_type != TransactionTypeEnum.REVERSAL,
                ~has_reversal_transaction(),
            )
            .group_by("week")
        )

        result = await self.session.execute(query)
        return {row.week: row.transactions_count for row in result}
