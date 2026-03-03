from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import UserStatusEnum
from app.repositories.database import Base

if TYPE_CHECKING:
    from app.models.balance import UserBalance


class User(Base):
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    status: Mapped[UserStatusEnum] = mapped_column(
        Enum(
            UserStatusEnum, values_callable=lambda x: [e.value for e in x], native_enum=False, name="user_status_enum"
        ),
        default=UserStatusEnum.ACTIVE,
    )

    user_balances: Mapped[list["UserBalance"]] = relationship("UserBalance", back_populates="owner")

    def __repr__(self):
        return f"User(email={self.email})"
