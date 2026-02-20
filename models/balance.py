from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.enums import CurrencyEnum
from database import Base

if TYPE_CHECKING:
    from models.user import User


class UserBalance(Base):
    __tablename__ = "user_balances"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    currency: Mapped[CurrencyEnum] = mapped_column(
        Enum(
            CurrencyEnum,
            values_callable=lambda currencies: [currency.value for currency in currencies],
            native_enum=False,
            name="currency_enum",
        ),
        default=CurrencyEnum.USD,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), server_default=text("0.00"))
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    owner: Mapped["User"] = relationship("User", back_populates="user_balances", uselist=False)

    __table_args__ = (UniqueConstraint("user_id", "currency", name="user_balance_user_currency_unique"),)

    def __repr__(self):
        return f"UserBalance(user_id={self.user_id}, currency={self.currency})"
