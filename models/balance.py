from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from models.user import User


class UserBalance(Base):
    __tablename__ = "user_balances"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    currency: Mapped[str | None] = mapped_column()
    amount: Mapped[Decimal | None] = mapped_column(Numeric(precision=15, scale=2))
    created: Mapped[datetime | None] = mapped_column()
    UniqueConstraint("user_id", "currency", name="user_balance_user_currency_unique")

    owner: Mapped["User"] = relationship("User", back_populates="user_balances", uselist=False)
