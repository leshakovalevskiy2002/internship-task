"""initial

Revision ID: 14f10399d17b
Revises: 
Create Date: 2026-08-12 15:11:02.222744

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "14f10399d17b"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "users",
        sa.Column("email", sa.String(length=100), nullable=False),
        sa.Column("status", sa.Enum("ACTIVE", "BLOCKED", name="user_status_enum", native_enum=False), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_table(
        "transactions",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "currency",
            sa.Enum(
                "USD",
                "EUR",
                "AUD",
                "CAD",
                "ARS",
                "PLN",
                "BTC",
                "ETH",
                "DOGE",
                "USDT",
                name="transaction_currency_enum",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(precision=15, scale=2), server_default=sa.text("0.00"), nullable=False),
        sa.Column(
            "status", sa.Enum("PROCESSED", "ROLLBACKED", name="transaction_status", native_enum=False), nullable=False
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_transactions_user_id"), "transactions", ["user_id"], unique=False)
    op.create_table(
        "user_balances",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "currency",
            sa.Enum(
                "USD",
                "EUR",
                "AUD",
                "CAD",
                "ARS",
                "PLN",
                "BTC",
                "ETH",
                "DOGE",
                "USDT",
                name="currency_enum",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(precision=15, scale=2), server_default=sa.text("0.00"), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "currency", name="user_balance_user_currency_unique"),
    )
    op.create_index(op.f("ix_user_balances_user_id"), "user_balances", ["user_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_user_balances_user_id"), table_name="user_balances")
    op.drop_table("user_balances")
    op.drop_index(op.f("ix_transactions_user_id"), table_name="transactions")
    op.drop_table("transactions")
    op.drop_table("users")
