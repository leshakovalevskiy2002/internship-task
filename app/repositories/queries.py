from datetime import date

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.core.enums import CurrencyEnum, TransactionTypeEnum
from app.models.transaction import Transaction
from app.models.user import User

EXCHANGE_RATES_TO_USD = {
    CurrencyEnum.USD: 1,
    CurrencyEnum.EUR: 0.9342,
    CurrencyEnum.AUD: 0.5447,
    CurrencyEnum.CAD: 0.6162,
    CurrencyEnum.ARS: 0.0009,
    CurrencyEnum.PLN: 0.2343,
    CurrencyEnum.BTC: 100000.0,
    CurrencyEnum.ETH: 3557.3476,
    CurrencyEnum.DOGE: 0.3627,
    CurrencyEnum.USDT: 0.9709,
}


async def get_registered_users_count(session: AsyncSession, start_date: date, end_date: date):
    query = select(func.count(User.id)).select_from(User).where(func.date(User.created).between(start_date, end_date))
    result = await session.execute(query)
    registered_users = result.scalar()
    return registered_users


async def get_registered_and_deposit_users_count(session: AsyncSession, start_date: date, end_date: date):
    query = (
        select(func.count(User.email.distinct()))
        .select_from(User)
        .join(Transaction, User.id == Transaction.user_id)
        .where(
            func.date(User.created).between(start_date, end_date),
            Transaction.operation_type == TransactionTypeEnum.DEPOSIT,
            func.date(Transaction.created).between(start_date, end_date),
        )
    )
    result = await session.execute(query)
    deposits = result.scalar()
    return deposits


async def get_registered_and_not_roll_backed_deposit_users_count(
    session: AsyncSession, start_date: date, end_date: date
):
    reversal_transaction = aliased(Transaction)
    subquery = select(reversal_transaction).where(Transaction.id == reversal_transaction.reversal_of_id).exists()

    query = (
        select(func.count(User.email.distinct()))
        .select_from(User)
        .join(Transaction, User.id == Transaction.user_id)
        .where(
            func.date(User.created).between(start_date, end_date),
            Transaction.operation_type == TransactionTypeEnum.DEPOSIT,
            func.date(Transaction.created).between(start_date, end_date),
            ~subquery,
        )
    )
    result = await session.execute(query)
    deposits = result.scalar()
    return deposits


async def get_not_roll_backed_deposit_amount(session: AsyncSession, start_date: date, end_date: date):
    rate_case = case(
        (Transaction.currency == CurrencyEnum.USD.value, EXCHANGE_RATES_TO_USD[CurrencyEnum.USD]),
        (Transaction.currency == CurrencyEnum.EUR.value, EXCHANGE_RATES_TO_USD[CurrencyEnum.EUR]),
        (Transaction.currency == CurrencyEnum.AUD.value, EXCHANGE_RATES_TO_USD[CurrencyEnum.AUD]),
        (Transaction.currency == CurrencyEnum.CAD.value, EXCHANGE_RATES_TO_USD[CurrencyEnum.CAD]),
        (Transaction.currency == CurrencyEnum.ARS.value, EXCHANGE_RATES_TO_USD[CurrencyEnum.ARS]),
        (Transaction.currency == CurrencyEnum.PLN.value, EXCHANGE_RATES_TO_USD[CurrencyEnum.PLN]),
        (Transaction.currency == CurrencyEnum.BTC.value, EXCHANGE_RATES_TO_USD[CurrencyEnum.BTC]),
        (Transaction.currency == CurrencyEnum.ETH.value, EXCHANGE_RATES_TO_USD[CurrencyEnum.ETH]),
        (Transaction.currency == CurrencyEnum.DOGE.value, EXCHANGE_RATES_TO_USD[CurrencyEnum.DOGE]),
        (Transaction.currency == CurrencyEnum.USDT.value, EXCHANGE_RATES_TO_USD[CurrencyEnum.USDT]),
        else_=0,
    )

    reversal_transaction = aliased(Transaction)
    subquery = select(reversal_transaction).where(Transaction.id == reversal_transaction.reversal_of_id).exists()

    query = (
        select(func.coalesce(func.sum(Transaction.amount * rate_case), 0))
        .select_from(Transaction)
        .where(
            func.date(Transaction.created).between(start_date, end_date),
            Transaction.operation_type == TransactionTypeEnum.DEPOSIT,
            ~subquery,
        )
    )
    result = await session.execute(query)
    not_roll_backed_deposits = result.scalar()
    return not_roll_backed_deposits


async def get_not_roll_backed_withdraw_amount(session: AsyncSession, start_date: date, end_date: date):
    rate_case = case(
        (Transaction.currency == CurrencyEnum.USD.value, EXCHANGE_RATES_TO_USD[CurrencyEnum.USD]),
        (Transaction.currency == CurrencyEnum.EUR.value, EXCHANGE_RATES_TO_USD[CurrencyEnum.EUR]),
        (Transaction.currency == CurrencyEnum.AUD.value, EXCHANGE_RATES_TO_USD[CurrencyEnum.AUD]),
        (Transaction.currency == CurrencyEnum.CAD.value, EXCHANGE_RATES_TO_USD[CurrencyEnum.CAD]),
        (Transaction.currency == CurrencyEnum.ARS.value, EXCHANGE_RATES_TO_USD[CurrencyEnum.ARS]),
        (Transaction.currency == CurrencyEnum.PLN.value, EXCHANGE_RATES_TO_USD[CurrencyEnum.PLN]),
        (Transaction.currency == CurrencyEnum.BTC.value, EXCHANGE_RATES_TO_USD[CurrencyEnum.BTC]),
        (Transaction.currency == CurrencyEnum.ETH.value, EXCHANGE_RATES_TO_USD[CurrencyEnum.ETH]),
        (Transaction.currency == CurrencyEnum.DOGE.value, EXCHANGE_RATES_TO_USD[CurrencyEnum.DOGE]),
        (Transaction.currency == CurrencyEnum.USDT.value, EXCHANGE_RATES_TO_USD[CurrencyEnum.USDT]),
        else_=0,
    )

    reversal_transaction = aliased(Transaction)
    subquery = select(reversal_transaction).where(Transaction.id == reversal_transaction.reversal_of_id).exists()

    query = (
        select(func.coalesce(func.sum(Transaction.amount * rate_case), 0))
        .select_from(Transaction)
        .where(
            func.date(Transaction.created).between(start_date, end_date),
            Transaction.operation_type == TransactionTypeEnum.WITHDRAW,
            ~subquery,
        )
    )
    result = await session.execute(query)
    not_roll_backed_withdraws = result.scalar()
    return not_roll_backed_withdraws


async def get_transactions_count(session: AsyncSession, start_date: date, end_date: date):
    query = (
        select(func.count(Transaction.id))
        .select_from(Transaction)
        .where(
            func.date(Transaction.created).between(start_date, end_date),
            Transaction.operation_type != TransactionTypeEnum.REVERSAL,
        )
    )
    result = await session.execute(query)
    transactions_count = result.scalar()
    return transactions_count


async def get_not_roll_backed_transactions_count(session: AsyncSession, start_date: date, end_date: date):
    reversal_transaction = aliased(Transaction)
    subquery = select(reversal_transaction).where(Transaction.id == reversal_transaction.reversal_of_id).exists()

    query = (
        select(func.count(Transaction.id))
        .select_from(Transaction)
        .where(
            func.date(Transaction.created).between(start_date, end_date),
            Transaction.operation_type != TransactionTypeEnum.REVERSAL,
            ~subquery,
        )
    )
    result = await session.execute(query)
    not_roll_backed_transactions_count = result.scalar()
    return not_roll_backed_transactions_count
