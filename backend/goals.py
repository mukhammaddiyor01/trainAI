"""Owner-scoped weight goals with a stable, server-selected starting weight."""

from uuid import UUID

from sqlalchemy import select

from backend.database import session_scope
from backend.models import Goal, Profile
from backend.services.goals import GoalDetails, validate_goal


class GoalProfileRequired(ValueError):
    """A saved basic profile is required before recording a goal."""


def read_goal(user_id: UUID) -> GoalDetails | None:
    with session_scope() as session:
        goal = session.get(Goal, user_id)
        if goal is None:
            return None
        return GoalDetails(goal.direction, goal.starting_weight_kg, goal.target_weight_kg)


def save_goal(user_id: UUID, direction: str, target_weight_kg: float | None) -> GoalDetails:
    with session_scope() as session:
        # Serialize goal saves with profile edits and concurrent goal requests.
        profile = session.scalar(select(Profile).where(Profile.user_id == user_id).with_for_update())
        if profile is None:
            raise GoalProfileRequired("Save your basic profile before setting a goal.")
        goal = session.get(Goal, user_id)
        if goal is not None and goal.direction == direction and goal.target_weight_kg == target_weight_kg:
            return GoalDetails(goal.direction, goal.starting_weight_kg, goal.target_weight_kg)
        details = validate_goal(direction, profile.weight_kg, target_weight_kg)
        if goal is None:
            goal = Goal(user_id=user_id)
            session.add(goal)
        goal.direction = details.direction
        goal.starting_weight_kg = details.starting_weight_kg
        goal.target_weight_kg = details.target_weight_kg
    return details
