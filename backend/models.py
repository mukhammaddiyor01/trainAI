"""Authentication records; fitness records arrive with their features."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Float, SmallInteger, String, Text, func
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
