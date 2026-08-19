from decimal import Decimal

from app.core.enums import CurrencyEnum

EXCHANGE_RATES_TO_USD = {
    CurrencyEnum.USD: Decimal("1"),
    CurrencyEnum.EUR: Decimal("0.9342"),
    CurrencyEnum.AUD: Decimal("0.5447"),
    CurrencyEnum.CAD: Decimal("0.6162"),
    CurrencyEnum.ARS: Decimal("0.0009"),
    CurrencyEnum.PLN: Decimal("0.2343"),
    CurrencyEnum.BTC: Decimal("100000.0"),
    CurrencyEnum.ETH: Decimal("3557.3476"),
    CurrencyEnum.DOGE: Decimal("0.3627"),
    CurrencyEnum.USDT: Decimal("0.9709"),
}
