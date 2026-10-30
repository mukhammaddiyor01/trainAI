"""Strict HTTP contracts; secrets never belong in public response models."""

from uuid import UUID
from typing import Literal

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
