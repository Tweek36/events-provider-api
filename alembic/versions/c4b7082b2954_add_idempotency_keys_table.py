"""add_idempotency_keys_table

Revision ID: c4b7082b2954
Revises: 7ce77e7cf2aa
Create Date: 2026-05-20 11:18:11.250808

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as pg

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c4b7082b2954"
down_revision: str | Sequence[str] | None = "7ce77e7cf2aa"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "idempotency_keys",
        sa.Column("id", pg.UUID(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("ticket_id", pg.UUID(), nullable=False),
        sa.Column("request_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key"),
        sa.Index("ix_idempotency_keys_idempotency_key", "idempotency_key"),
        sa.Index("ix_idempotency_keys_created_at", "created_at"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("idempotency_keys")
