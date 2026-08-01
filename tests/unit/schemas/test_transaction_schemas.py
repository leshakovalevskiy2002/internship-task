from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.core.enums import CurrencyEnum, TransactionTypeEnum
from app.schemas.transactions import CreateTransactionModel


class TestCreateTransactionSchema:
    @pytest.mark.parametrize("amount", [Decimal("0.00"), Decimal("-0.01")])
    def test_amount_validation_failed(self, amount: Decimal):
        with pytest.raises(ValidationError):
            CreateTransactionModel(
                currency=CurrencyEnum.USD, operation_type=TransactionTypeEnum.WITHDRAW, amount=amount
            )

    @pytest.mark.parametrize("amount", [Decimal("0.01"), Decimal("200.45")])
    def test_amount_validation_succeeds(self, amount: Decimal):
        model = CreateTransactionModel(
            currency=CurrencyEnum.USD, operation_type=TransactionTypeEnum.WITHDRAW, amount=amount
        )

        assert model.amount == amount
