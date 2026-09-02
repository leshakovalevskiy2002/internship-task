"""change transaction domain

Revision ID: fac626350d6d
Revises: 14f10399d17b
Create Date: 2026-09-02 02:43:14.964028

"""

from typing import Sequence, Union
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "fac626350d6d"
down_revision: Union[str, Sequence[str], None] = "14f10399d17b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


CURRENCIES = ("USD", "EUR", "AUD", "CAD", "ARS", "PLN", "BTC", "ETH", "DOGE", "USDT")


def upgrade() -> None:
    bind = op.get_bind()

    currency_enum = postgresql.ENUM(*CURRENCIES, name="currency_enum")
    transaction_type_enum = postgresql.ENUM("DEPOSIT", "WITHDRAW", "REVERSAL", name="transaction_type_enum")
    transaction_status_enum = postgresql.ENUM("PROCESSED", name="transaction_status_enum")
    user_status_enum = postgresql.ENUM("ACTIVE", "BLOCKED", name="user_status_enum")

    currency_enum.create(bind, checkfirst=True)
    transaction_type_enum.create(bind, checkfirst=True)
    transaction_status_enum.create(bind, checkfirst=True)
    user_status_enum.create(bind, checkfirst=True)

    op.add_column("transactions", sa.Column("type", transaction_type_enum, nullable=True))
    op.add_column("transactions", sa.Column("reversal_of_id", sa.Uuid(), nullable=True))

    op.execute(
        """
        UPDATE transactions
        SET type = CASE
            WHEN amount > 0 THEN 'DEPOSIT'
            ELSE 'WITHDRAW'
        END::transaction_type_enum
        """
    )

    roll_backed_transactions = (
        bind.execute(
            sa.text(
                """
            SELECT id, user_id, currency, amount, created, updated
            FROM transactions
            WHERE status = 'ROLLBACKED'
            """
            )
        )
        .mappings()
        .all()
    )

    op.execute(
        """
        UPDATE transactions
        SET amount = ABS(amount)
        """
    )

    for transaction in roll_backed_transactions:
        bind.execute(
            sa.text(
                """
                INSERT INTO transactions (id, user_id, currency, type, amount, status, reversal_of_id, created, updated)
                VALUES (
                    :id,
                    :user_id,
                    CAST(:currency AS currency_enum),
                    CAST(:type AS transaction_type_enum),
                    :amount,
                    CAST(:status AS transaction_status_enum),
                    :reversal_of_id,
                    :created,
                    :updated
                )
                """
            ),
            {
                "id": uuid4(),
                "user_id": transaction["user_id"],
                "currency": transaction["currency"],
                "type": "REVERSAL",
                "amount": abs(transaction["amount"]),
                "status": "PROCESSED",
                "reversal_of_id": transaction["id"],
                "created": transaction["created"],
                "updated": transaction["updated"],
            },
        )

    op.execute(
        """
        UPDATE transactions
        SET status = 'PROCESSED'
        WHERE status = 'ROLLBACKED'
        """
    )

    op.alter_column(
        "users",
        "status",
        existing_type=sa.VARCHAR(),
        type_=user_status_enum,
        existing_nullable=False,
        server_default=sa.text("'ACTIVE'"),
        postgresql_using="status::user_status_enum",
    )

    op.alter_column(
        "transactions",
        "currency",
        existing_type=sa.VARCHAR(length=4),
        type_=currency_enum,
        existing_nullable=False,
        server_default=sa.text("'USD'"),
        postgresql_using="currency::currency_enum",
    )

    op.alter_column(
        "transactions",
        "status",
        existing_type=sa.VARCHAR(),
        type_=transaction_status_enum,
        existing_nullable=False,
        server_default=sa.text("'PROCESSED'"),
        postgresql_using="status::transaction_status_enum",
    )

    op.alter_column(
        "user_balances",
        "currency",
        existing_type=sa.VARCHAR(length=4),
        type_=currency_enum,
        server_default=sa.text("'USD'"),
        existing_nullable=False,
        postgresql_using="currency::currency_enum",
    )

    op.alter_column("transactions", "type", nullable=False)

    op.create_unique_constraint(
        "transactions_reversal_of_id_key",
        "transactions",
        ["reversal_of_id"],
    )

    op.create_foreign_key(
        "transactions_reversal_of_id_fkey",
        "transactions",
        "transactions",
        ["reversal_of_id"],
        ["id"],
    )

    op.create_check_constraint(
        "transaction_amount_positive",
        "transactions",
        "amount > 0",
    )

    op.create_check_constraint(
        "user_balance_amount_is_positive",
        "user_balances",
        "amount >= 0",
    )

    op.drop_constraint(
        "user_balances_user_id_fkey",
        "user_balances",
        type_="foreignkey",
    )

    op.create_foreign_key(
        "user_balances_user_id_fkey",
        "user_balances",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_index(op.f("ix_user_balances_user_id"), table_name="user_balances")


def downgrade() -> None:
    bind = op.get_bind()

    reversed_transaction_ids = list(
        bind.execute(
            sa.text(
                """
                SELECT t.id
                FROM transactions t
                JOIN transactions r
                    ON r.reversal_of_id = t.id
                WHERE r.type = 'REVERSAL'
            """
            )
        ).scalars()
    )

    op.execute(
        """
        DELETE FROM transactions
        WHERE type = 'REVERSAL'
        """
    )

    op.drop_constraint(
        "transaction_amount_positive",
        "transactions",
        type_="check",
    )

    op.execute(
        """
        UPDATE transactions
        SET amount = CASE
            WHEN type = 'WITHDRAW' THEN -ABS(amount)
            ELSE ABS(amount)
        END
        """
    )

    op.drop_constraint(
        "user_balance_amount_is_positive",
        "user_balances",
        type_="check",
    )

    op.drop_constraint(
        "transactions_reversal_of_id_key",
        "transactions",
        type_="unique",
    )

    op.drop_constraint(
        "transactions_reversal_of_id_fkey",
        "transactions",
        type_="foreignkey",
    )

    op.drop_constraint(
        "user_balances_user_id_fkey",
        "user_balances",
        type_="foreignkey",
    )

    op.create_foreign_key(
        "user_balances_user_id_fkey",
        "user_balances",
        "users",
        ["user_id"],
        ["id"],
    )

    op.create_index(
        op.f("ix_user_balances_user_id"),
        "user_balances",
        ["user_id"],
        unique=False,
    )

    op.alter_column(
        "users",
        "status",
        existing_type=postgresql.ENUM(
            "ACTIVE",
            "BLOCKED",
            name="user_status_enum",
        ),
        type_=sa.VARCHAR(),
        existing_nullable=False,
        postgresql_using="status::text",
    )

    op.alter_column(
        "transactions",
        "currency",
        existing_type=postgresql.ENUM(
            *CURRENCIES,
            name="currency_enum",
        ),
        type_=sa.VARCHAR(length=4),
        existing_nullable=False,
        postgresql_using="currency::text",
    )

    op.alter_column(
        "transactions",
        "status",
        existing_type=postgresql.ENUM(
            "PROCESSED",
            name="transaction_status_enum",
        ),
        type_=sa.VARCHAR(),
        existing_nullable=False,
        postgresql_using="status::text",
    )

    op.alter_column(
        "user_balances",
        "currency",
        existing_type=postgresql.ENUM(
            *CURRENCIES,
            name="currency_enum",
        ),
        type_=sa.VARCHAR(length=4),
        existing_nullable=False,
        postgresql_using="currency::text",
    )

    if reversed_transaction_ids:
        for transaction_id in reversed_transaction_ids:
            bind.execute(
                sa.text(
                    """
                    UPDATE transactions
                    SET status = 'ROLLBACKED'
                    WHERE id = :id
                    """
                ),
                {"id": transaction_id},
            )

    op.drop_column(
        "transactions",
        "reversal_of_id",
    )

    op.drop_column(
        "transactions",
        "type",
    )

    postgresql.ENUM(
        "ACTIVE",
        "BLOCKED",
        name="user_status_enum",
    ).drop(bind, checkfirst=True)

    postgresql.ENUM(
        "PROCESSED",
        name="transaction_status_enum",
    ).drop(bind, checkfirst=True)

    postgresql.ENUM(
        "DEPOSIT",
        "WITHDRAW",
        "REVERSAL",
        name="transaction_type_enum",
    ).drop(bind, checkfirst=True)

    postgresql.ENUM(
        *CURRENCIES,
        name="currency_enum",
    ).drop(bind, checkfirst=True)
