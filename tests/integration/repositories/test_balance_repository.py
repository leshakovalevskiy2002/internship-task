from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select

from app.core.enums import CurrencyEnum
from app.models.balance import UserBalance
from app.repositories.balances import BalanceRepository


class TestBalanceRepository:
    async def test_create_default_balances_for_user(self, balance_repository: BalanceRepository, user_factory):
        session = balance_repository.session

        user = await user_factory()
        await balance_repository.create_default_balances_for_user(user.id)
        await session.flush()

        balances = await session.scalars(select(UserBalance).where(UserBalance.user_id == user.id))
        list_balances = list(balances)

        assert len(list_balances) == len(CurrencyEnum)
        assert {balance.currency for balance in list_balances} == set(CurrencyEnum)
        assert all(balance.user_id == user.id for balance in list_balances)
        assert all(balance.amount == Decimal("0.00") for balance in list_balances)

    async def test_get_user_balance_returns_balance(self, balance_repository, user_balance_factory):
        balance = await user_balance_factory()

        result = await balance_repository.get_user_balance_for_update(balance.user_id, CurrencyEnum.USD)

        assert result is not None
        assert result.id == balance.id
        assert result.user_id == balance.user_id
        assert result.currency == CurrencyEnum.USD

    async def test_get_user_balance_returns_none_if_not_exists(self, balance_repository):
        result = await balance_repository.get_user_balance_for_update(uuid4(), CurrencyEnum.USD)
        assert result is None

    async def test_get_user_balance_filters_by_user(self, balance_repository, user_balance_factory):
        balance1 = await user_balance_factory(currency=CurrencyEnum.USD)
        balance2 = await user_balance_factory(currency=CurrencyEnum.USD)

        result = await balance_repository.get_user_balance_for_update(balance1.user_id, CurrencyEnum.USD)

        assert result is not None
        assert result.id == balance1.id
        assert result.user_id == balance1.user_id
        assert result.id != balance2.id

    async def test_get_user_balance_filters_by_currency(self, balance_repository, user_factory, user_balance_factory):
        user = await user_factory()

        usd_balance = await user_balance_factory(user=user, currency=CurrencyEnum.USD)
        eur_balance = await user_balance_factory(user=user, currency=CurrencyEnum.EUR)

        result = await balance_repository.get_user_balance_for_update(usd_balance.user_id, CurrencyEnum.EUR)

        assert result is not None
        assert result.id == eur_balance.id
        assert result.currency == CurrencyEnum.EUR
