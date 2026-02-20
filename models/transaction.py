from datetime import datetime
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    currency: Mapped[str | None] = mapped_column()
    amount: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), nullable=True)
    status: Mapped[str | None] = mapped_column()
    created: Mapped[datetime | None] = mapped_column()
