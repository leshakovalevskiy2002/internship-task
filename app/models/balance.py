from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Numeric, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import CurrencyEnum
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class UserBalance(Base):
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    currency: Mapped[CurrencyEnum] = mapped_column(
        Enum(
            CurrencyEnum,
            name="currency_enum",
            native_enum=True,
        ),
        server_default=CurrencyEnum.USD.value,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), server_default=text("0.00"))

    owner: Mapped["User"] = relationship("User", back_populates="user_balances")

    __table_args__ = (
        UniqueConstraint("user_id", "currency", name="user_balance_user_currency_unique"),
        CheckConstraint("amount >= 0", name="user_balance_amount_is_positive"),
    )

    def __repr__(self):
        return f"UserBalance(user_id={self.user_id}, currency={self.currency})"
