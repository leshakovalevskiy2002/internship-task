from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Numeric, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import CurrencyEnum, TransactionStatusEnum
from app.repositories.database import Base

if TYPE_CHECKING:
    pass


class Transaction(Base):
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    currency: Mapped[CurrencyEnum] = mapped_column(
        Enum(
            CurrencyEnum,
            values_callable=lambda currencies: [currency.value for currency in currencies],
            native_enum=False,
            name="transaction_currency_enum",
        ),
        default=CurrencyEnum.USD,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), server_default=text("0.00"))
    status: Mapped[TransactionStatusEnum] = mapped_column(
        Enum(
            TransactionStatusEnum,
            values_callable=lambda statuses: [status.value for status in statuses],
            native_enum=False,
            name="transaction_status",
        ),
        default=TransactionStatusEnum.PROCESSED,
    )
