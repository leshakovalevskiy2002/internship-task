from decimal import Decimal
from uuid import uuid4

from sqlalchemy import ScalarResult, select

from app.core.enums import CurrencyEnum
from app.models.balance import UserBalance
from app.repositories.balances import BalanceRepository


class TestBalanceRepository:
    async def test_create_default_balances_for_user(self, balance_repository: BalanceRepository, user_factory):
        session = balance_repository.session

        user = await user_factory()
        await balance_repository.create_default_balances_for_user(user.id)
        await session.flush()

        balances: ScalarResult[UserBalance] = await session.scalars(select(UserBalance))
        list_balances = list(balances)
        currency_balances = [balance.currency for balance in list_balances]
        amount_balances = [balance.amount for balance in list_balances]

        assert sorted(currency_balances) == sorted(list(CurrencyEnum))
        assert amount_balances == [Decimal("0.00")] * 10

    async def test_get_user_balance_returns_balance(self, balance_repository, user_balance_factory):
        balance = await user_balance_factory()

        result = await balance_repository.get_user_balance(balance.user_id, CurrencyEnum.USD)

        assert result is not None
        assert result.id == balance.id
        assert result.user_id == balance.user_id
        assert result.currency == CurrencyEnum.USD

    async def test_get_user_balance_returns_none_if_not_exists(self, balance_repository):
        result = await balance_repository.get_user_balance(uuid4(), CurrencyEnum.USD)
        assert result is None

    async def test_get_user_balance_filters_by_user(self, balance_repository, user_balance_factory):
        await user_balance_factory(currency=CurrencyEnum.USD)

        result = await balance_repository.get_user_balance(uuid4(), CurrencyEnum.USD)
        assert result is None
