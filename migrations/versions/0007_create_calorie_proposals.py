"""Store owner-scoped, pending calorie proposal snapshots only."""

from alembic import op
import sqlalchemy as sa

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "calorie_proposals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("profile_age", sa.SmallInteger(), nullable=False),
        sa.Column("profile_height_cm", sa.Float(), nullable=False),
        sa.Column("profile_weight_kg", sa.Float(), nullable=False),
        sa.Column("goal_direction", sa.String(16), nullable=False),
        sa.Column("goal_starting_weight_kg", sa.Float(), nullable=False),
        sa.Column("goal_target_weight_kg", sa.Float(), nullable=True),
        sa.Column("equation_sex", sa.String(24), nullable=False),
        sa.Column("activity_category", sa.String(24), nullable=False),
        sa.Column("context", sa.String(24), nullable=False),
        sa.Column("adjustment_kcal", sa.SmallInteger(), nullable=False),
        sa.Column("signed_adjustment_kcal", sa.SmallInteger(), nullable=False),
        sa.Column("maintenance_kcal_per_day", sa.Float(), nullable=False),
        sa.Column("preview_kcal_per_day", sa.Float(), nullable=False),
        sa.Column("energy_method_version", sa.String(40), nullable=False),
        sa.Column("policy_version", sa.String(64), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("status = 'pending'", name="ck_proposal_pending"),
        sa.CheckConstraint("profile_age BETWEEN 19 AND 120", name="ck_proposal_age"),
        sa.CheckConstraint("profile_height_cm BETWEEN 50 AND 300", name="ck_proposal_height"),
        sa.CheckConstraint("profile_weight_kg BETWEEN 20 AND 500", name="ck_proposal_weight"),
        sa.CheckConstraint("goal_direction IN ('gain', 'lose', 'maintain')", name="ck_proposal_direction"),
        sa.CheckConstraint("goal_starting_weight_kg BETWEEN 20 AND 500", name="ck_proposal_starting_weight"),
        sa.CheckConstraint("goal_target_weight_kg IS NULL OR goal_target_weight_kg BETWEEN 20 AND 500", name="ck_proposal_target_weight"),
        sa.CheckConstraint("(goal_direction = 'maintain' AND goal_target_weight_kg IS NULL) OR "
                           "(goal_direction = 'gain' AND goal_target_weight_kg IS NOT NULL AND goal_target_weight_kg > goal_starting_weight_kg) OR "
                           "(goal_direction = 'lose' AND goal_target_weight_kg IS NOT NULL AND goal_target_weight_kg < goal_starting_weight_kg)",
                           name="ck_proposal_goal_shape"),
        sa.CheckConstraint("equation_sex IN ('male', 'female')", name="ck_proposal_equation_sex"),
        sa.CheckConstraint("activity_category IN ('inactive', 'low_active', 'active', 'very_active')", name="ck_proposal_activity"),
        sa.CheckConstraint("context = 'general_adult'", name="ck_proposal_context"),
        sa.CheckConstraint("adjustment_kcal BETWEEN 0 AND 250", name="ck_proposal_magnitude"),
        sa.CheckConstraint("(goal_direction = 'maintain' AND adjustment_kcal = 0 AND signed_adjustment_kcal = 0) OR "
                           "(goal_direction = 'gain' AND adjustment_kcal > 0 AND signed_adjustment_kcal = adjustment_kcal) OR "
                           "(goal_direction = 'lose' AND adjustment_kcal > 0 AND signed_adjustment_kcal = -adjustment_kcal)",
                           name="ck_proposal_signed_adjustment"),
        sa.CheckConstraint("maintenance_kcal_per_day > 0", name="ck_proposal_maintenance"),
        sa.CheckConstraint("preview_kcal_per_day >= 1500", name="ck_proposal_preview_floor"),
        sa.CheckConstraint("energy_method_version = 'dri-2023-adult-eer-v1'", name="ck_proposal_energy_version"),
        sa.CheckConstraint("policy_version = 'manual-adjustment-preview-2026-11-04-v1'", name="ck_proposal_policy_version"),
    )
    op.create_index("ix_calorie_proposals_user_id", "calorie_proposals", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_calorie_proposals_user_id", table_name="calorie_proposals")
    op.drop_table("calorie_proposals")
