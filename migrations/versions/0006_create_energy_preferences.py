"""Add explicit private energy preferences; do not backfill existing profiles."""

from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "energy_preferences",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("equation_sex", sa.String(24), nullable=False),
        sa.Column("activity_category", sa.String(24), nullable=False),
        sa.Column("context", sa.String(24), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
        sa.CheckConstraint("equation_sex IN ('male', 'female', 'unsure')", name="ck_energy_equation_sex"),
        sa.CheckConstraint("activity_category IN ('inactive', 'low_active', 'active', 'very_active', 'unsure')", name="ck_energy_activity"),
        sa.CheckConstraint("context IN ('general_adult', 'pregnant', 'breastfeeding', 'clinical', 'unsure')", name="ck_energy_context"),
    )


def downgrade() -> None:
    op.drop_table("energy_preferences")
