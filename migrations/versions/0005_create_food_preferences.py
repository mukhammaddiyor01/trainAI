"""Add private food preferences without changing existing profile records."""

from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "food_preferences",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("diet", sa.String(16), nullable=False),
        sa.Column("allergy_status", sa.String(16), nullable=False),
        sa.Column("allergies", sa.ARRAY(sa.String(64)), nullable=False),
        sa.Column("budget_level", sa.String(16), nullable=False),
        sa.Column("prep_minutes", sa.SmallInteger(), nullable=False),
        sa.Column("meal_minutes", sa.ARRAY(sa.SmallInteger()), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
        sa.CheckConstraint("diet IN ('mixed', 'vegetarian', 'vegan')", name="ck_food_diet"),
        sa.CheckConstraint("allergy_status IN ('unsure', 'none_reported', 'listed')", name="ck_food_allergy_status"),
        sa.CheckConstraint("budget_level IN ('economical', 'standard', 'flexible')", name="ck_food_budget"),
        sa.CheckConstraint("prep_minutes BETWEEN 0 AND 180", name="ck_food_preparation"),
        sa.CheckConstraint("cardinality(allergies) <= 20 AND array_position(allergies, NULL) IS NULL "
                           "AND (cardinality(allergies) = 0 OR array_ndims(allergies) = 1)", name="ck_food_allergy_array"),
        sa.CheckConstraint("(allergy_status = 'listed' AND cardinality(allergies) > 0) OR "
                           "(allergy_status IN ('unsure', 'none_reported') AND cardinality(allergies) = 0)", name="ck_food_allergy_consistency"),
        sa.CheckConstraint("cardinality(meal_minutes) BETWEEN 1 AND 8 AND array_ndims(meal_minutes) = 1 "
                           "AND array_position(meal_minutes, NULL) IS NULL "
                           "AND 0 <= ALL(meal_minutes) AND 1439 >= ALL(meal_minutes)", name="ck_food_meal_times"),
    )


def downgrade() -> None:
    op.drop_table("food_preferences")
