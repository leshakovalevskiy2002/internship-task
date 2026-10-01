from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import CurrencyEnum, TransactionStatusEnum, TransactionTypeEnum
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class Transaction(Base):
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    currency: Mapped[CurrencyEnum] = mapped_column(
        Enum(
            CurrencyEnum,
            name="currency_enum",
            native_enum=True,
        ),
        server_default=CurrencyEnum.USD.value,
    )
    operation_type: Mapped[TransactionTypeEnum] = mapped_column(
        "type",
        Enum(
            TransactionTypeEnum,
            name="transaction_type_enum",
            native_enum=True,
        ),
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2))
    status: Mapped[TransactionStatusEnum] = mapped_column(
        Enum(
            TransactionStatusEnum,
            name="transaction_status_enum",
            native_enum=True,
        ),
        server_default=TransactionStatusEnum.PROCESSED.value,
    )
    reversal_of_id: Mapped[UUID | None] = mapped_column(ForeignKey("transactions.id"), unique=True)

    owner: Mapped["User"] = relationship("User", back_populates="transactions")
    original_transaction: Mapped["Transaction | None"] = relationship(
        "Transaction",
        back_populates="reversal",
        remote_side="Transaction.id",
    )
    reversal: Mapped["Transaction | None"] = relationship(
        "Transaction",
        back_populates="original_transaction",
        uselist=False,
    )

    __table_args__ = (CheckConstraint("amount > 0", name="transaction_amount_positive"),)
