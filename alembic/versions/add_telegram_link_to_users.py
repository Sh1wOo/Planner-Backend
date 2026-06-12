"""add telegram link fields to users

Revision ID: add_telegram_link_to_users
Revises: None
Create Date: 2026-06-12
"""

from alembic import op
import sqlalchemy as sa

revision = "add_telegram_link_to_users"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("telegram_id", sa.BigInteger(), nullable=True))
    op.add_column("users", sa.Column("telegram_username", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("telegram_first_name", sa.String(length=255), nullable=True))
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_telegram_id", table_name="users")
    op.drop_column("users", "telegram_first_name")
    op.drop_column("users", "telegram_username")
    op.drop_column("users", "telegram_id")
