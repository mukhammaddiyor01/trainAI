"""Bounded explicit-request calorie arithmetic; never activates or persists a target."""

from dataclasses import dataclass
import math

from backend.services.energy_estimation import estimate_adult_energy
from backend.services.energy_preferences import EnergyPreferencesDetails
from backend.services.goals import GoalDetails, validate_goal
from backend.services.profiles import ProfileDetails

CALORIE_PREVIEW_POLICY_VERSION = "manual-adjustment-preview-2026-11-04-v1"
MAX_ADJUSTMENT_KCAL = 250
MAX_ADJUSTMENT_FRACTION = 0.10
MIN_PREVIEW_KCAL = 1500
MIN_PREVIEW_BMI = 18.5
MAX_PREVIEW_BMI = 40


class InvalidCalorieAdjustment(ValueError):
    """The requested magnitude exceeds the explicit experimental preview bounds."""


class CaloriePreviewUnavailable(ValueError):
    """The profile or saved goal is outside the supported preview scope."""


@dataclass(frozen=True)
class CalorieAdjustmentPreview:
    maintenance_kcal_per_day: float
    adjustment_kcal_per_day: int
    preview_kcal_per_day: float
    goal_direction: str
    energy_method_version: str
    policy_version: str
    status: str = "preview"


def preview_calorie_adjustment(profile: ProfileDetails, preferences: EnergyPreferencesDetails,
                               goal: GoalDetails, adjustment_kcal: int) -> CalorieAdjustmentPreview:
    if type(adjustment_kcal) is not int or not 0 <= adjustment_kcal <= MAX_ADJUSTMENT_KCAL:
        raise InvalidCalorieAdjustment("Enter a whole-number adjustment magnitude from 0 to 250 kcal/day.")
    if type(goal) is not GoalDetails:
        raise CaloriePreviewUnavailable("A saved weight goal is required before previewing an adjustment.")
    # Preserve the goal's recorded baseline when checking its original consistency.
    goal = validate_goal(goal.direction, goal.starting_weight_kg, goal.target_weight_kg)
    estimate = estimate_adult_energy(profile, preferences)
    if goal.direction == "maintain":
        if adjustment_kcal != 0:
            raise InvalidCalorieAdjustment("A maintenance preview requires an explicit zero adjustment.")
    else:
        if adjustment_kcal == 0:
            raise InvalidCalorieAdjustment("A gain or loss preview requires an explicit positive adjustment magnitude.")
        if ((goal.direction == "gain" and goal.target_weight_kg <= profile.weight_kg)
                or (goal.direction == "lose" and goal.target_weight_kg >= profile.weight_kg)):
            raise CaloriePreviewUnavailable("Review your saved goal against your current weight before an adjustment.")
    # Screening bounds limit this preview; they do not diagnose or establish suitability.
    weights = (profile.weight_kg,) if goal.target_weight_kg is None else (profile.weight_kg, goal.target_weight_kg)
    for weight in weights:
        bmi = weight / (profile.height_cm / 100) ** 2
        if not MIN_PREVIEW_BMI <= bmi < MAX_PREVIEW_BMI:
            raise CaloriePreviewUnavailable("The current or target weight is outside the supported preview scope.")
    if adjustment_kcal > estimate.energy_kcal_per_day * MAX_ADJUSTMENT_FRACTION:
        raise InvalidCalorieAdjustment("The adjustment must not exceed 10 percent of the current maintenance estimate.")
    signed_adjustment = -adjustment_kcal if goal.direction == "lose" else adjustment_kcal
    preview = math.fsum((estimate.energy_kcal_per_day, signed_adjustment))
    if not math.isfinite(preview) or preview < MIN_PREVIEW_KCAL:
        raise CaloriePreviewUnavailable("The resulting preview is below the supported 1500 kcal/day floor.")
    return CalorieAdjustmentPreview(estimate.energy_kcal_per_day, signed_adjustment, preview,
                                    goal.direction, estimate.method_version, CALORIE_PREVIEW_POLICY_VERSION)
