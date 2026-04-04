"""add paid flags to income and expense

Revision ID: 7f3d2f6a9c11
Revises: 51d1b2c4b873
Create Date: 2026-04-03 21:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "7f3d2f6a9c11"
down_revision = "51d1b2c4b873"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("income", schema=None) as batch_op:
        batch_op.add_column(sa.Column("is_paid", sa.Boolean(), nullable=False, server_default=sa.false()))

    with op.batch_alter_table("expense", schema=None) as batch_op:
        batch_op.add_column(sa.Column("is_paid", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade():
    with op.batch_alter_table("expense", schema=None) as batch_op:
        batch_op.drop_column("is_paid")

    with op.batch_alter_table("income", schema=None) as batch_op:
        batch_op.drop_column("is_paid")
