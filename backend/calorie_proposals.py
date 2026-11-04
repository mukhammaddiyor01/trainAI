"""Create private pending proposals from locked, current source rows."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import select

from backend.database import session_scope
from backend.models import CalorieProposal, EnergyPreferences, Goal, Profile
from backend.services.calorie_preview import preview_calorie_adjustment
from backend.services.energy_preferences import validate_energy_preferences
from backend.services.goals import validate_goal
from backend.services.profiles import validate_profile


class CalorieProposalInputsRequired(ValueError):
    """All three saved inputs are required before storing a proposal."""


@dataclass(frozen=True)
class PendingCalorieProposal:
    id: UUID
    user_id: UUID
    created_at: datetime
    status: str
    profile_age: int
    profile_height_cm: float
    profile_weight_kg: float
    goal_direction: str
    goal_starting_weight_kg: float
    goal_target_weight_kg: float | None
    equation_sex: str
    activity_category: str
    context: str
    adjustment_kcal: int
    signed_adjustment_kcal: int
    maintenance_kcal_per_day: float
    preview_kcal_per_day: float
    energy_method_version: str
    policy_version: str


def _plain_proposal(row: CalorieProposal) -> PendingCalorieProposal:
    return PendingCalorieProposal(
        row.id, row.user_id, row.created_at, row.status, row.profile_age,
        row.profile_height_cm, row.profile_weight_kg, row.goal_direction,
        row.goal_starting_weight_kg, row.goal_target_weight_kg, row.equation_sex,
        row.activity_category, row.context, row.adjustment_kcal,
        row.signed_adjustment_kcal, row.maintenance_kcal_per_day,
        row.preview_kcal_per_day, row.energy_method_version, row.policy_version,
    )


def create_calorie_proposal(user_id: UUID, adjustment_kcal: int) -> PendingCalorieProposal:
    with session_scope() as session:
        # Profile edits and goal saves use this row; lock it before dependent rows.
        profile_row = session.scalar(select(Profile).where(Profile.user_id == user_id).with_for_update())
        if profile_row is None:
            raise CalorieProposalInputsRequired("Save your profile, energy preferences, and goal first.")
        rows = session.execute(select(EnergyPreferences, Goal).join(
            Goal, Goal.user_id == EnergyPreferences.user_id,
        ).where(EnergyPreferences.user_id == user_id).with_for_update()).one_or_none()
        if rows is None:
            raise CalorieProposalInputsRequired("Save your profile, energy preferences, and goal first.")
        energy_row, goal_row = rows
        profile = validate_profile(profile_row.age, profile_row.height_cm, profile_row.weight_kg, profile_row.timezone)
        preferences = validate_energy_preferences(energy_row.equation_sex, energy_row.activity_category, energy_row.context)
        goal = validate_goal(goal_row.direction, goal_row.starting_weight_kg, goal_row.target_weight_kg)
        preview = preview_calorie_adjustment(profile, preferences, goal, adjustment_kcal)
        row = CalorieProposal(
            id=uuid4(), user_id=user_id, status="pending",
            profile_age=profile.age, profile_height_cm=profile.height_cm,
            profile_weight_kg=profile.weight_kg, goal_direction=goal.direction,
            goal_starting_weight_kg=goal.starting_weight_kg,
            goal_target_weight_kg=goal.target_weight_kg,
            equation_sex=preferences.equation_sex,
            activity_category=preferences.activity_category, context=preferences.context,
            adjustment_kcal=adjustment_kcal,
            signed_adjustment_kcal=preview.adjustment_kcal_per_day,
            maintenance_kcal_per_day=preview.maintenance_kcal_per_day,
            preview_kcal_per_day=preview.preview_kcal_per_day,
            energy_method_version=preview.energy_method_version,
            policy_version=preview.policy_version,
        )
        session.add(row)
        session.flush()
        details = _plain_proposal(row)
    return details


def read_calorie_proposal(user_id: UUID, proposal_id: UUID) -> PendingCalorieProposal | None:
    with session_scope() as session:
        row = session.scalar(select(CalorieProposal).where(
            CalorieProposal.user_id == user_id, CalorieProposal.id == proposal_id,
        ))
        return None if row is None else _plain_proposal(row)
