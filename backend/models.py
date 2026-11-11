"""Authentication records; fitness records arrive with their features."""

from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import ARRAY, CheckConstraint, Date, DateTime, ForeignKey, ForeignKeyConstraint, Float, Index, Integer, SmallInteger, String, Text, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("username ~ '^[a-z0-9_]{3,32}$'", name="ck_users_username"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    username: Mapped[str] = mapped_column(String(32), unique=True)
    password_hash: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LoginSession(Base):
    __tablename__ = "login_sessions"
    __table_args__ = (
        CheckConstraint("expires_at > created_at", name="ck_sessions_expiry"),
    )

    token_digest: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class Profile(Base):
    __tablename__ = "profiles"
    __table_args__ = (
        CheckConstraint("age BETWEEN 18 AND 120", name="ck_profiles_age"),
        CheckConstraint("height_cm BETWEEN 50 AND 300", name="ck_profiles_height"),
        CheckConstraint("weight_kg BETWEEN 20 AND 500", name="ck_profiles_weight"),
        CheckConstraint("length(timezone) BETWEEN 1 AND 64", name="ck_profiles_timezone"),
    )

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    age: Mapped[int] = mapped_column(SmallInteger)
    height_cm: Mapped[float] = mapped_column(Float)
    weight_kg: Mapped[float] = mapped_column(Float)
    timezone: Mapped[str] = mapped_column(String(64))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class WeightEntry(Base):
    __tablename__ = "weight_entries"
    __table_args__ = (
        CheckConstraint("weight_kg BETWEEN 20 AND 500", name="ck_weight_entries_weight"),
    )

    user_id: Mapped[UUID] = mapped_column(ForeignKey("profiles.user_id", ondelete="CASCADE"), primary_key=True)
    local_date: Mapped[date] = mapped_column(Date, primary_key=True)
    weight_kg: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Goal(Base):
    __tablename__ = "goals"
    __table_args__ = (
        CheckConstraint("direction IN ('gain', 'lose', 'maintain')", name="ck_goals_direction"),
        CheckConstraint("starting_weight_kg BETWEEN 20 AND 500", name="ck_goals_starting_weight"),
        CheckConstraint("target_weight_kg IS NULL OR target_weight_kg BETWEEN 20 AND 500", name="ck_goals_target_weight"),
        CheckConstraint(
            "(direction = 'maintain' AND target_weight_kg IS NULL) OR "
            "(direction = 'gain' AND target_weight_kg IS NOT NULL AND target_weight_kg > starting_weight_kg) OR "
            "(direction = 'lose' AND target_weight_kg IS NOT NULL AND target_weight_kg < starting_weight_kg)",
            name="ck_goals_target_direction",
        ),
    )

    user_id: Mapped[UUID] = mapped_column(ForeignKey("profiles.user_id", ondelete="CASCADE"), primary_key=True)
    direction: Mapped[str] = mapped_column(String(16))
    starting_weight_kg: Mapped[float] = mapped_column(Float)
    target_weight_kg: Mapped[float | None] = mapped_column(Float)


class TrainingPreferences(Base):
    __tablename__ = "training_preferences"
    __table_args__ = (
        CheckConstraint("experience IN ('beginner', 'intermediate', 'advanced')", name="ck_training_experience"),
        CheckConstraint("activity IN ('mostly_seated', 'lightly_active', 'moderately_active', 'very_active')", name="ck_training_activity"),
        CheckConstraint("equipment_mask BETWEEN 0 AND 127", name="ck_training_equipment"),
        CheckConstraint("weekday_mask BETWEEN 1 AND 127", name="ck_training_weekdays"),
        CheckConstraint("session_minutes BETWEEN 10 AND 180", name="ck_training_duration"),
    )

    user_id: Mapped[UUID] = mapped_column(ForeignKey("profiles.user_id", ondelete="CASCADE"), primary_key=True)
    experience: Mapped[str] = mapped_column(String(16))
    activity: Mapped[str] = mapped_column(String(24))
    equipment_mask: Mapped[int] = mapped_column(SmallInteger)
    weekday_mask: Mapped[int] = mapped_column(SmallInteger)
    session_minutes: Mapped[int] = mapped_column(SmallInteger)


class MovementLimitations(Base):
    __tablename__ = "movement_limitations"
    __table_args__ = (
        CheckConstraint("status IN ('unsure', 'none_reported', 'needs_adaptation')",
                        name="ck_movement_limitations_status"),
    )

    user_id: Mapped[UUID] = mapped_column(ForeignKey("profiles.user_id", ondelete="CASCADE"), primary_key=True)
    status: Mapped[str] = mapped_column(String(20))


class FoodPreferences(Base):
    __tablename__ = "food_preferences"
    __table_args__ = (
        CheckConstraint("diet IN ('mixed', 'vegetarian', 'vegan')", name="ck_food_diet"),
        CheckConstraint("allergy_status IN ('unsure', 'none_reported', 'listed')", name="ck_food_allergy_status"),
        CheckConstraint("budget_level IN ('economical', 'standard', 'flexible')", name="ck_food_budget"),
        CheckConstraint("prep_minutes BETWEEN 0 AND 180", name="ck_food_preparation"),
        CheckConstraint("cardinality(allergies) <= 20 AND array_position(allergies, NULL) IS NULL "
                        "AND (cardinality(allergies) = 0 OR array_ndims(allergies) = 1)", name="ck_food_allergy_array"),
        CheckConstraint("(allergy_status = 'listed' AND cardinality(allergies) > 0) OR "
                        "(allergy_status IN ('unsure', 'none_reported') AND cardinality(allergies) = 0)", name="ck_food_allergy_consistency"),
        CheckConstraint("cardinality(meal_minutes) BETWEEN 1 AND 8 AND array_ndims(meal_minutes) = 1 "
                        "AND array_position(meal_minutes, NULL) IS NULL "
                        "AND 0 <= ALL(meal_minutes) AND 1439 >= ALL(meal_minutes)", name="ck_food_meal_times"),
    )

    user_id: Mapped[UUID] = mapped_column(ForeignKey("profiles.user_id", ondelete="CASCADE"), primary_key=True)
    diet: Mapped[str] = mapped_column(String(16))
    allergy_status: Mapped[str] = mapped_column(String(16))
    allergies: Mapped[list[str]] = mapped_column(ARRAY(String(64)))
    budget_level: Mapped[str] = mapped_column(String(16))
    prep_minutes: Mapped[int] = mapped_column(SmallInteger)
    meal_minutes: Mapped[list[int]] = mapped_column(ARRAY(SmallInteger))


class EnergyPreferences(Base):
    __tablename__ = "energy_preferences"
    __table_args__ = (
        CheckConstraint("equation_sex IN ('male', 'female', 'unsure')", name="ck_energy_equation_sex"),
        CheckConstraint("activity_category IN ('inactive', 'low_active', 'active', 'very_active', 'unsure')", name="ck_energy_activity"),
        CheckConstraint("context IN ('general_adult', 'pregnant', 'breastfeeding', 'clinical', 'unsure')", name="ck_energy_context"),
    )

    user_id: Mapped[UUID] = mapped_column(ForeignKey("profiles.user_id", ondelete="CASCADE"), primary_key=True)
    equation_sex: Mapped[str] = mapped_column(String(24))
    activity_category: Mapped[str] = mapped_column(String(24))
    context: Mapped[str] = mapped_column(String(24))


class CalorieProposal(Base):
    __tablename__ = "calorie_proposals"
    __table_args__ = (
        UniqueConstraint("user_id", "id", name="uq_proposal_owner_id"),
        CheckConstraint("(status = 'pending' AND approved_at IS NULL) OR "
                        "(status = 'approved' AND approved_at IS NOT NULL)", name="ck_proposal_lifecycle"),
        CheckConstraint("profile_age BETWEEN 19 AND 120", name="ck_proposal_age"),
        CheckConstraint("profile_height_cm BETWEEN 50 AND 300", name="ck_proposal_height"),
        CheckConstraint("profile_weight_kg BETWEEN 20 AND 500", name="ck_proposal_weight"),
        CheckConstraint("goal_direction IN ('gain', 'lose', 'maintain')", name="ck_proposal_direction"),
        CheckConstraint("goal_starting_weight_kg BETWEEN 20 AND 500", name="ck_proposal_starting_weight"),
        CheckConstraint("goal_target_weight_kg IS NULL OR goal_target_weight_kg BETWEEN 20 AND 500", name="ck_proposal_target_weight"),
        CheckConstraint("(goal_direction = 'maintain' AND goal_target_weight_kg IS NULL) OR "
                        "(goal_direction = 'gain' AND goal_target_weight_kg IS NOT NULL AND goal_target_weight_kg > goal_starting_weight_kg) OR "
                        "(goal_direction = 'lose' AND goal_target_weight_kg IS NOT NULL AND goal_target_weight_kg < goal_starting_weight_kg)",
                        name="ck_proposal_goal_shape"),
        CheckConstraint("equation_sex IN ('male', 'female')", name="ck_proposal_equation_sex"),
        CheckConstraint("activity_category IN ('inactive', 'low_active', 'active', 'very_active')", name="ck_proposal_activity"),
        CheckConstraint("context = 'general_adult'", name="ck_proposal_context"),
        CheckConstraint("adjustment_kcal BETWEEN 0 AND 250", name="ck_proposal_magnitude"),
        CheckConstraint("(goal_direction = 'maintain' AND adjustment_kcal = 0 AND signed_adjustment_kcal = 0) OR "
                        "(goal_direction = 'gain' AND adjustment_kcal > 0 AND signed_adjustment_kcal = adjustment_kcal) OR "
                        "(goal_direction = 'lose' AND adjustment_kcal > 0 AND signed_adjustment_kcal = -adjustment_kcal)",
                        name="ck_proposal_signed_adjustment"),
        CheckConstraint("maintenance_kcal_per_day > 0", name="ck_proposal_maintenance"),
        CheckConstraint("preview_kcal_per_day >= 1500", name="ck_proposal_preview_floor"),
        CheckConstraint("energy_method_version = 'dri-2023-adult-eer-v1'", name="ck_proposal_energy_version"),
        CheckConstraint("policy_version = 'manual-adjustment-preview-2026-11-04-v1'", name="ck_proposal_policy_version"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("profiles.user_id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    status: Mapped[str] = mapped_column(String(16))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    base_version_id: Mapped[UUID | None] = mapped_column(nullable=True)
    profile_age: Mapped[int] = mapped_column(SmallInteger)
    profile_height_cm: Mapped[float] = mapped_column(Float)
    profile_weight_kg: Mapped[float] = mapped_column(Float)
    goal_direction: Mapped[str] = mapped_column(String(16))
    goal_starting_weight_kg: Mapped[float] = mapped_column(Float)
    goal_target_weight_kg: Mapped[float | None] = mapped_column(Float)
    equation_sex: Mapped[str] = mapped_column(String(24))
    activity_category: Mapped[str] = mapped_column(String(24))
    context: Mapped[str] = mapped_column(String(24))
    adjustment_kcal: Mapped[int] = mapped_column(SmallInteger)
    signed_adjustment_kcal: Mapped[int] = mapped_column(SmallInteger)
    maintenance_kcal_per_day: Mapped[float] = mapped_column(Float)
    preview_kcal_per_day: Mapped[float] = mapped_column(Float)
    energy_method_version: Mapped[str] = mapped_column(String(40))
    policy_version: Mapped[str] = mapped_column(String(64))


class CalorieTargetVersion(Base):
    __tablename__ = "calorie_target_versions"
    __table_args__ = (
        ForeignKeyConstraint(["user_id", "proposal_id"],
                             ["calorie_proposals.user_id", "calorie_proposals.id"], ondelete="CASCADE"),
        UniqueConstraint("user_id", "version", name="uq_calorie_target_owner_version"),
        UniqueConstraint("proposal_id", name="uq_calorie_target_proposal"),
        CheckConstraint("version >= 1", name="ck_calorie_target_version"),
        CheckConstraint("(status = 'active' AND superseded_at IS NULL) OR "
                        "(status = 'superseded' AND superseded_at IS NOT NULL)", name="ck_calorie_target_lifecycle"),
        CheckConstraint("target_kcal_per_day >= 1500", name="ck_calorie_target_floor"),
        Index("uq_calorie_target_active_owner", "user_id", unique=True,
              postgresql_where=text("status = 'active'")),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("profiles.user_id", ondelete="CASCADE"))
    proposal_id: Mapped[UUID] = mapped_column()
    version: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(16))
    target_kcal_per_day: Mapped[float] = mapped_column(Float)
    approved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
