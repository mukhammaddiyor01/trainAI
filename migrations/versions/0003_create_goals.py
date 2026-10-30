"""Create one owner-scoped current goal with a starting-weight snapshot."""

from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "goals",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("direction", sa.String(16), nullable=False),
        sa.Column("starting_weight_kg", sa.Float(), nullable=False),
        sa.Column("target_weight_kg", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
        sa.CheckConstraint("direction IN ('gain', 'lose', 'maintain')", name="ck_goals_direction"),
        sa.CheckConstraint("starting_weight_kg BETWEEN 20 AND 500", name="ck_goals_starting_weight"),
        sa.CheckConstraint("target_weight_kg IS NULL OR target_weight_kg BETWEEN 20 AND 500", name="ck_goals_target_weight"),
        sa.CheckConstraint(
            "(direction = 'maintain' AND target_weight_kg IS NULL) OR "
            "(direction = 'gain' AND target_weight_kg IS NOT NULL AND target_weight_kg > starting_weight_kg) OR "
            "(direction = 'lose' AND target_weight_kg IS NOT NULL AND target_weight_kg < starting_weight_kg)",
            name="ck_goals_target_direction",
        ),
    )


def downgrade() -> None:
    op.drop_table("goals")
