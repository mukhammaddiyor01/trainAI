"""Create one private basic profile per user."""

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "profiles",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("age", sa.SmallInteger(), nullable=False),
        sa.Column("height_cm", sa.Float(), nullable=False),
        sa.Column("weight_kg", sa.Float(), nullable=False),
        sa.Column("timezone", sa.String(64), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
        sa.CheckConstraint("age BETWEEN 18 AND 120", name="ck_profiles_age"),
        sa.CheckConstraint("height_cm BETWEEN 50 AND 300", name="ck_profiles_height"),
        sa.CheckConstraint("weight_kg BETWEEN 20 AND 500", name="ck_profiles_weight"),
        sa.CheckConstraint("length(timezone) BETWEEN 1 AND 64", name="ck_profiles_timezone"),
    )


def downgrade() -> None:
    op.drop_table("profiles")
