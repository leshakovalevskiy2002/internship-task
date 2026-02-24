from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, func, text
from sqlalchemy.orm import Mapped, mapped_column

from core.enums import CurrencyEnum, TransactionStatusEnum
from database import Base

if TYPE_CHECKING:
    from models.user import User


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    currency: Mapped[CurrencyEnum] = mapped_column(
        Enum(
            CurrencyEnum,
            values_callable=lambda currencies: [currency.value for currency in currencies],
            native_enum=False,
            name="transaction_currency_enum",
        )
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), server_default=text("0.00"))
    status: Mapped[TransactionStatusEnum] = mapped_column(
        Enum(
            TransactionStatusEnum,
            values_callable=lambda statuses: [status.value for status in statuses],
            native_enum=False,
            name="transaction_status",
        )
    )
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
