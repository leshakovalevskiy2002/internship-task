from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.enums import UserStatusEnum
from database import Base

if TYPE_CHECKING:
    from models.balance import UserBalance


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    status: Mapped[UserStatusEnum] = mapped_column(
        Enum(
            UserStatusEnum, values_callable=lambda x: [e.value for e in x], native_enum=False, name="user_status_enum"
        ),
        default=UserStatusEnum.ACTIVE,
    )
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user_balances: Mapped[list["UserBalance"]] = relationship("UserBalance", back_populates="owner")

    def __repr__(self):
        return f"User(email={self.email})"
