"""add tournament

Revision ID: 99414b600ea1
Revises: a03568fd9a1e
Create Date: 2026-07-13 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "99414b600ea1"
down_revision = "a03568fd9a1e"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "tournament",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("field_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("format", sa.String(length=20), nullable=False),
        sa.Column("customer_name", sa.String(length=120), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.Column("deposit_paid", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["field_id"], ["field.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    with op.batch_alter_table("reservation", schema=None) as batch_op:
        batch_op.add_column(sa.Column("tournament_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key("fk_reservation_tournament_id", "tournament", ["tournament_id"], ["id"])


def downgrade():
    with op.batch_alter_table("reservation", schema=None) as batch_op:
        batch_op.drop_constraint("fk_reservation_tournament_id", type_="foreignkey")
        batch_op.drop_column("tournament_id")

    op.drop_table("tournament")
