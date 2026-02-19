from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from models.balance import UserBalance


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str | None] = mapped_column(unique=True)
    status: Mapped[str | None] = mapped_column()
    created: Mapped[datetime | None] = mapped_column()

    user_balances: Mapped[list["UserBalance"]] = relationship("UserBalance", back_populates="owner")
