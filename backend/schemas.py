"""Strict HTTP contracts; secrets never belong in public response models."""

from datetime import datetime
from uuid import UUID
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator

from backend.services.accounts import MAX_PASSWORD_LENGTH, MIN_PASSWORD_LENGTH, validate_password


class Credentials(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", hide_input_in_errors=True)

    username: str = Field(min_length=3, max_length=128)
    password: SecretStr = Field(min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH)

    @field_validator("password")
    @classmethod
    def valid_password_text(cls, value: SecretStr) -> SecretStr:
        password = value.get_secret_value()
        validate_password(password)
        try:
            password.encode("utf-8")
        except UnicodeError:
            raise ValueError("Use valid text for the password.") from None
        return value


class AccountResponse(BaseModel):
    # Ignore accidental extra fields so credentials cannot cross this boundary.
    model_config = ConfigDict(extra="ignore")

    user_id: UUID
    username: str = Field(min_length=3, max_length=32, pattern=r"^[a-z0-9_]+$")


class ProfileInput(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", hide_input_in_errors=True)

    age: int = Field(ge=18, le=120)
    height_cm: float = Field(ge=50, le=300, allow_inf_nan=False)
    weight_kg: float = Field(ge=20, le=500, allow_inf_nan=False)
    timezone: str = Field(min_length=1, max_length=64)


class ProfileResponse(ProfileInput):
    """An explicit four-field response without owner IDs or internal metadata."""


class GoalInput(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", hide_input_in_errors=True)

    direction: Literal["gain", "lose", "maintain"]
    target_weight_kg: float | None = Field(default=None, ge=20, le=500, allow_inf_nan=False)


class GoalResponse(GoalInput):
    starting_weight_kg: float = Field(ge=20, le=500, allow_inf_nan=False)


class TrainingPreferencesInput(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", hide_input_in_errors=True)

    experience: Literal["beginner", "intermediate", "advanced"]
    activity: Literal["mostly_seated", "lightly_active", "moderately_active", "very_active"]
    equipment: list[Literal["dumbbells", "barbell", "resistance_bands", "bench", "pull_up_bar", "cable_machine", "weight_machines"]] = Field(max_length=7)
    weekdays: list[int] = Field(min_length=1, max_length=7)
    session_minutes: int = Field(ge=10, le=180)


class TrainingPreferencesResponse(TrainingPreferencesInput):
    """Only the five preference fields; no ownership or storage internals."""


class MovementLimitationsInput(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", hide_input_in_errors=True)

    status: Literal["unsure", "none_reported", "needs_adaptation"]


class MovementLimitationsResponse(MovementLimitationsInput):
    """Only the explicit self-report; no owner or health-history fields."""


class FoodPreferencesInput(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", hide_input_in_errors=True)

    diet: Literal["mixed", "vegetarian", "vegan"]
    allergy_status: Literal["unsure", "none_reported", "listed"]
    allergies: list[Annotated[str, Field(min_length=1, max_length=64)]] = Field(max_length=20)
    budget_level: Literal["economical", "standard", "flexible"]
    prep_minutes: int = Field(ge=0, le=180)
    meal_times: list[Annotated[str, Field(min_length=5, max_length=5)]] = Field(min_length=1, max_length=8)


class FoodPreferencesResponse(FoodPreferencesInput):
    """Six public preference fields, without owner IDs or persistence internals."""


class EnergyPreferencesInput(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", hide_input_in_errors=True)

    equation_sex: Literal["male", "female", "unsure"]
    activity_category: Literal["inactive", "low_active", "active", "very_active", "unsure"]
    context: Literal["general_adult", "pregnant", "breastfeeding", "clinical", "unsure"]


class EnergyPreferencesResponse(EnergyPreferencesInput):
    """Only the three selected choices; no owner, calorie target, or storage metadata."""


class AdultEnergyEstimateResponse(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", hide_input_in_errors=True)

    energy_kcal_per_day: float = Field(gt=0, allow_inf_nan=False)
    method_version: Literal["dri-2023-adult-eer-v1"]
    equation_sex: Literal["male", "female"]
    activity_category: Literal["inactive", "low_active", "active", "very_active"]


class CaloriePreviewInput(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", hide_input_in_errors=True)

    adjustment_kcal: int = Field(ge=0, le=250)


class CaloriePreviewResponse(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", hide_input_in_errors=True)

    maintenance_kcal_per_day: float = Field(gt=0, allow_inf_nan=False)
    adjustment_kcal_per_day: int = Field(ge=-250, le=250)
    preview_kcal_per_day: float = Field(ge=1500, allow_inf_nan=False)
    goal_direction: Literal["gain", "lose", "maintain"]
    energy_method_version: Literal["dri-2023-adult-eer-v1"]
    policy_version: Literal["manual-adjustment-preview-2026-11-04-v1"]
    status: Literal["preview"]


class CalorieProposalResponse(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", hide_input_in_errors=True)

    proposal_id: UUID
    created_at: datetime
    status: Literal["pending", "approved"]
    maintenance_kcal_per_day: float = Field(gt=0, allow_inf_nan=False)
    adjustment_kcal_per_day: int = Field(ge=-250, le=250)
    preview_kcal_per_day: float = Field(ge=1500, allow_inf_nan=False)
    goal_direction: Literal["gain", "lose", "maintain"]
    energy_method_version: Literal["dri-2023-adult-eer-v1"]
    policy_version: Literal["manual-adjustment-preview-2026-11-04-v1"]


class CalorieProposalListResponse(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", hide_input_in_errors=True)

    items: list[CalorieProposalResponse] = Field(max_length=20)
    next_before: UUID | None


class CalorieApprovalInput(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", hide_input_in_errors=True)

    confirm: bool = Field(strict=True)

    @field_validator("confirm")
    @classmethod
    def requires_explicit_true(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError("Explicit confirmation is required.")
        return value


class CalorieTargetResponse(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", hide_input_in_errors=True)

    target_id: UUID
    proposal_id: UUID
    version: int = Field(ge=1)
    status: Literal["active", "superseded"]
    target_kcal_per_day: float = Field(ge=1500, allow_inf_nan=False)
    approved_at: datetime


class CalorieTargetListResponse(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", hide_input_in_errors=True)

    items: list[CalorieTargetResponse] = Field(max_length=20)
