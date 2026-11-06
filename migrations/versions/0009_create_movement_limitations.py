"""Store an explicit movement limitation self-report without backfilling profiles."""

from alembic import op
import sqlalchemy as sa

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "movement_limitations",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
        sa.CheckConstraint("status IN ('unsure', 'none_reported', 'needs_adaptation')",
                           name="ck_movement_limitations_status"),
    )


def downgrade() -> None:
    op.drop_table("movement_limitations")
