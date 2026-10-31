"""Create one private training-preference record per profile."""

from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "training_preferences",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("experience", sa.String(16), nullable=False),
        sa.Column("activity", sa.String(24), nullable=False),
        sa.Column("equipment_mask", sa.SmallInteger(), nullable=False),
        sa.Column("weekday_mask", sa.SmallInteger(), nullable=False),
        sa.Column("session_minutes", sa.SmallInteger(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
        sa.CheckConstraint("experience IN ('beginner', 'intermediate', 'advanced')", name="ck_training_experience"),
        sa.CheckConstraint("activity IN ('mostly_seated', 'lightly_active', 'moderately_active', 'very_active')", name="ck_training_activity"),
        sa.CheckConstraint("equipment_mask BETWEEN 0 AND 127", name="ck_training_equipment"),
        sa.CheckConstraint("weekday_mask BETWEEN 1 AND 127", name="ck_training_weekdays"),
        sa.CheckConstraint("session_minutes BETWEEN 10 AND 180", name="ck_training_duration"),
    )


def downgrade() -> None:
    op.drop_table("training_preferences")
