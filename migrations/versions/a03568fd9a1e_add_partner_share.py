"""add partner share

Revision ID: a03568fd9a1e
Revises: 7f3d2f6a9c11
Create Date: 2026-07-12 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "a03568fd9a1e"
down_revision = "7f3d2f6a9c11"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "partner_share",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("partner_name", sa.String(length=80), nullable=False),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("year", "month", "partner_name", name="uq_partner_share_period"),
    )


def downgrade():
    op.drop_table("partner_share")
