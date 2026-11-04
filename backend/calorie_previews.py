"""Read complete owner-scoped preview inputs in one snapshot; no target writes."""

from uuid import UUID
from sqlalchemy import select

from backend.database import session_scope
from backend.models import EnergyPreferences, Goal, Profile
from backend.services.energy_preferences import EnergyPreferencesDetails, validate_energy_preferences
from backend.services.goals import GoalDetails, validate_goal
from backend.services.profiles import ProfileDetails, validate_profile


def read_calorie_preview_inputs(user_id: UUID) -> tuple[ProfileDetails, EnergyPreferencesDetails, GoalDetails] | None:
    with session_scope() as session:
        rows = session.execute(select(Profile, EnergyPreferences, Goal).join(
            EnergyPreferences, EnergyPreferences.user_id == Profile.user_id,
        ).join(Goal, Goal.user_id == Profile.user_id).where(Profile.user_id == user_id)).one_or_none()
        if rows is None:
            return None
        profile, preferences, goal = rows
        return (validate_profile(profile.age, profile.height_cm, profile.weight_kg, profile.timezone),
                validate_energy_preferences(preferences.equation_sex, preferences.activity_category, preferences.context),
                validate_goal(goal.direction, goal.starting_weight_kg, goal.target_weight_kg))
