"""Add domain-specific review framework fields.

Revision ID: 0003_add_review_framework
Revises: 0002_add_event_commodity
Create Date: 2026-05-25
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_add_review_framework"
down_revision = "0002_add_event_commodity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "alerts",
        sa.Column("review_framework", sa.String(length=30), nullable=False, server_default="THREAT_LEVEL"),
    )
    op.add_column("alerts", sa.Column("recommended_review_level", sa.String(length=10), nullable=True))
    op.add_column("alerts", sa.Column("confirmed_review_level", sa.String(length=10), nullable=True))
    op.execute("UPDATE alerts SET recommended_review_level = recommended_threat_level")
    op.execute("UPDATE alerts SET confirmed_review_level = confirmed_threat_level")
    op.add_column(
        "analyst_reviews",
        sa.Column("review_framework", sa.String(length=30), nullable=False, server_default="THREAT_LEVEL"),
    )
    op.add_column("analyst_reviews", sa.Column("review_level", sa.String(length=10), nullable=True))
    op.execute("UPDATE analyst_reviews SET review_level = threat_level")


def downgrade() -> None:
    op.drop_column("analyst_reviews", "review_level")
    op.drop_column("analyst_reviews", "review_framework")
    op.drop_column("alerts", "confirmed_review_level")
    op.drop_column("alerts", "recommended_review_level")
    op.drop_column("alerts", "review_framework")
