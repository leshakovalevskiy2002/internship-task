from sqlalchemy import case

from app.core.constants import EXCHANGE_RATES_TO_USD
from app.models.transaction import Transaction


def get_exchange_rate_case():
    return case(
        *[(Transaction.currency == currency.value, rate) for currency, rate in EXCHANGE_RATES_TO_USD.items()],
        else_=0,
    )
