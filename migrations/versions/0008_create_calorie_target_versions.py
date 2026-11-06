"""Add explicit approval lifecycle and one active calorie target per owner."""

from alembic import op
import sqlalchemy as sa

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("calorie_proposals", sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("calorie_proposals", sa.Column("base_version_id", sa.Uuid(), nullable=True))
    op.drop_constraint("ck_proposal_pending", "calorie_proposals", type_="check")
    op.create_check_constraint("ck_proposal_lifecycle", "calorie_proposals",
                               "(status = 'pending' AND approved_at IS NULL) OR "
                               "(status = 'approved' AND approved_at IS NOT NULL)")
    op.create_unique_constraint("uq_proposal_owner_id", "calorie_proposals", ["user_id", "id"])
    op.create_table(
        "calorie_target_versions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("proposal_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("target_kcal_per_day", sa.Float(), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("superseded_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.user_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id", "proposal_id"],
                                ["calorie_proposals.user_id", "calorie_proposals.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "version", name="uq_calorie_target_owner_version"),
        sa.UniqueConstraint("proposal_id", name="uq_calorie_target_proposal"),
        sa.CheckConstraint("version >= 1", name="ck_calorie_target_version"),
        sa.CheckConstraint("(status = 'active' AND superseded_at IS NULL) OR "
                           "(status = 'superseded' AND superseded_at IS NOT NULL)", name="ck_calorie_target_lifecycle"),
        sa.CheckConstraint("target_kcal_per_day >= 1500", name="ck_calorie_target_floor"),
    )
    op.create_index("uq_calorie_target_active_owner", "calorie_target_versions", ["user_id"],
                    unique=True, postgresql_where=sa.text("status = 'active'"))


def downgrade() -> None:
    op.drop_index("uq_calorie_target_active_owner", table_name="calorie_target_versions")
    op.drop_table("calorie_target_versions")
    op.execute("UPDATE calorie_proposals SET status = 'pending', approved_at = NULL WHERE status = 'approved'")
    op.drop_constraint("uq_proposal_owner_id", "calorie_proposals", type_="unique")
    op.drop_constraint("ck_proposal_lifecycle", "calorie_proposals", type_="check")
    op.create_check_constraint("ck_proposal_pending", "calorie_proposals", "status = 'pending'")
    op.drop_column("calorie_proposals", "base_version_id")
    op.drop_column("calorie_proposals", "approved_at")
