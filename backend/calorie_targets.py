"""Approve owner proposals into one active, versioned calorie target."""

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select

from backend.database import session_scope
from backend.models import CalorieProposal, CalorieTargetVersion, EnergyPreferences, Goal, Profile
from backend.services.calorie_preview import preview_calorie_adjustment
from backend.services.energy_preferences import validate_energy_preferences
from backend.services.goals import validate_goal
from backend.services.profiles import validate_profile


class CalorieProposalNotFound(ValueError):
    """The requested proposal is absent from the owner's account."""


class StaleCalorieProposal(ValueError):
    """Current inputs or the active version no longer match the saved proposal."""


@dataclass(frozen=True)
class CalorieTargetDetails:
    id: UUID
    user_id: UUID
    proposal_id: UUID
    version: int
    status: str
    target_kcal_per_day: float
    approved_at: datetime
    superseded_at: datetime | None


def _plain_target(row: CalorieTargetVersion) -> CalorieTargetDetails:
    approved_at = row.approved_at.astimezone(timezone.utc)
    superseded_at = None if row.superseded_at is None else row.superseded_at.astimezone(timezone.utc)
    return CalorieTargetDetails(row.id, row.user_id, row.proposal_id, row.version,
                                row.status, row.target_kcal_per_day, approved_at,
                                superseded_at)


def _matches_current(proposal: CalorieProposal, profile: Profile,
                     goal: Goal, energy: EnergyPreferences) -> bool:
    return (proposal.profile_age == profile.age
            and proposal.profile_height_cm == profile.height_cm
            and proposal.profile_weight_kg == profile.weight_kg
            and proposal.goal_direction == goal.direction
            and proposal.goal_starting_weight_kg == goal.starting_weight_kg
            and proposal.goal_target_weight_kg == goal.target_weight_kg
            and proposal.equation_sex == energy.equation_sex
            and proposal.activity_category == energy.activity_category
            and proposal.context == energy.context)


def approve_calorie_proposal(user_id: UUID, proposal_id: UUID) -> CalorieTargetDetails:
    with session_scope() as session:
        profile_row = session.scalar(select(Profile).where(Profile.user_id == user_id).with_for_update())
        if profile_row is None:
            raise CalorieProposalNotFound("Proposal not found.")
        proposal = session.scalar(select(CalorieProposal).where(
            CalorieProposal.user_id == user_id, CalorieProposal.id == proposal_id,
        ).with_for_update())
        if proposal is None:
            raise CalorieProposalNotFound("Proposal not found.")
        if proposal.status == "approved":
            existing = session.scalar(select(CalorieTargetVersion).where(
                CalorieTargetVersion.user_id == user_id,
                CalorieTargetVersion.proposal_id == proposal_id,
            ))
            if existing is None:
                raise StaleCalorieProposal("This proposal cannot be approved. Create a new preview.")
            return _plain_target(existing)
        if proposal.status != "pending":
            raise StaleCalorieProposal("This proposal cannot be approved. Create a new preview.")

        rows = session.execute(select(EnergyPreferences, Goal).join(
            Goal, Goal.user_id == EnergyPreferences.user_id,
        ).where(EnergyPreferences.user_id == user_id).with_for_update()).one_or_none()
        if rows is None:
            raise StaleCalorieProposal("Your saved inputs changed. Create a new preview.")
        energy_row, goal_row = rows
        active = session.scalar(select(CalorieTargetVersion).where(
            CalorieTargetVersion.user_id == user_id, CalorieTargetVersion.status == "active",
        ))
        if proposal.base_version_id != (None if active is None else active.id):
            raise StaleCalorieProposal("A newer target is active. Create a new preview.")
        if not _matches_current(proposal, profile_row, goal_row, energy_row):
            raise StaleCalorieProposal("Your saved inputs changed. Create a new preview.")
        try:
            profile = validate_profile(profile_row.age, profile_row.height_cm,
                                       profile_row.weight_kg, profile_row.timezone)
            goal = validate_goal(goal_row.direction, goal_row.starting_weight_kg,
                                 goal_row.target_weight_kg)
            energy = validate_energy_preferences(energy_row.equation_sex,
                                                 energy_row.activity_category, energy_row.context)
            preview = preview_calorie_adjustment(profile, energy, goal, proposal.adjustment_kcal)
        except ValueError:
            raise StaleCalorieProposal("This calculation is no longer available. Create a new preview.") from None
        if (preview.maintenance_kcal_per_day != proposal.maintenance_kcal_per_day
                or preview.adjustment_kcal_per_day != proposal.signed_adjustment_kcal
                or preview.preview_kcal_per_day != proposal.preview_kcal_per_day
                or preview.energy_method_version != proposal.energy_method_version
                or preview.policy_version != proposal.policy_version):
            raise StaleCalorieProposal("This calculation changed. Create a new preview.")

        now = datetime.now(timezone.utc)
        if active is not None:
            active.status = "superseded"
            active.superseded_at = now
            session.flush()
        version = CalorieTargetVersion(
            id=uuid4(), user_id=user_id, proposal_id=proposal_id,
            version=1 if active is None else active.version + 1,
            status="active", target_kcal_per_day=preview.preview_kcal_per_day,
            approved_at=now,
        )
        session.add(version)
        proposal.status = "approved"
        proposal.approved_at = now
        session.flush()
        return _plain_target(version)


def read_active_calorie_target(user_id: UUID) -> CalorieTargetDetails | None:
    with session_scope() as session:
        row = session.scalar(select(CalorieTargetVersion).where(
            CalorieTargetVersion.user_id == user_id,
            CalorieTargetVersion.status == "active",
        ))
        return None if row is None else _plain_target(row)
