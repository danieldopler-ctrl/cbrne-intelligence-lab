"""Add normalized chemical commodity field.

Revision ID: 0002_add_event_commodity
Revises: 0001_operational_core
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_add_event_commodity"
down_revision = "0001_operational_core"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("normalized_events", sa.Column("commodity", sa.String(length=255), nullable=True))
    op.create_index("ix_normalized_events_commodity", "normalized_events", ["commodity"])


def downgrade() -> None:
    op.drop_index("ix_normalized_events_commodity", table_name="normalized_events")
    op.drop_column("normalized_events", "commodity")
