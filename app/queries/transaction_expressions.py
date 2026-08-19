from sqlalchemy import case, select
from sqlalchemy.orm import aliased

from app.core.constants import EXCHANGE_RATES_TO_USD
from app.models.transaction import Transaction


def get_exchange_rate_case():
    return case(
        *[(Transaction.currency == currency.value, rate) for currency, rate in EXCHANGE_RATES_TO_USD.items()],
        else_=0,
    )


def has_reversal_transaction():
    reversal_transaction = aliased(Transaction)
    return select(reversal_transaction).where(Transaction.id == reversal_transaction.reversal_of_id).exists()
