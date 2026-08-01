from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import UserStatusEnum
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.balance import UserBalance
    from app.models.transaction import Transaction


class User(Base):
    email: Mapped[str] = mapped_column(String(100), unique=True)
    status: Mapped[UserStatusEnum] = mapped_column(
        Enum(
            UserStatusEnum,
            name="user_status_enum",
            native_enum=True,
        ),
        server_default=UserStatusEnum.ACTIVE.value,
    )

    user_balances: Mapped[list["UserBalance"]] = relationship(
        "UserBalance",
        back_populates="owner",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    transactions: Mapped[list["Transaction"]] = relationship("Transaction", back_populates="owner")

    def __repr__(self):
        return f"User(email={self.email})"
