"""Versioned adult DRI 2023 energy estimates; no goal offsets, plans, or side effects."""

from dataclasses import dataclass
import math
from types import MappingProxyType

from backend.services.energy_preferences import EnergyPreferencesDetails, validate_energy_preferences
from backend.services.profiles import ProfileDetails, validate_profile

ENERGY_METHOD_VERSION = "dri-2023-adult-eer-v1"
ENERGY_SOURCE_URL = "https://www.nationalacademies.org/read/26818/chapter/7"

# Table 5-16: constant, age (years), height (cm), weight (kg); result kcal/day.
_ADULT_EER_COEFFICIENTS = MappingProxyType({
    ("male", "inactive"): (753.07, -10.83, 6.50, 14.10),
    ("male", "low_active"): (581.47, -10.83, 8.30, 14.94),
    ("male", "active"): (1004.82, -10.83, 6.52, 15.91),
    ("male", "very_active"): (-517.88, -10.83, 15.61, 19.11),
    ("female", "inactive"): (584.90, -7.01, 5.72, 11.71),
    ("female", "low_active"): (575.77, -7.01, 6.60, 12.14),
    ("female", "active"): (710.25, -7.01, 6.54, 12.34),
    ("female", "very_active"): (511.83, -7.01, 9.07, 12.56),
})


class EnergyEstimateUnavailable(ValueError):
    """Explicit inputs or the current application scope do not permit an estimate."""


@dataclass(frozen=True)
class AdultEnergyEstimate:
    energy_kcal_per_day: float
    method_version: str
    equation_sex: str
    activity_category: str


def estimate_adult_energy(profile: ProfileDetails,
                          preferences: EnergyPreferencesDetails) -> AdultEnergyEstimate:
    if type(profile) is not ProfileDetails or type(preferences) is not EnergyPreferencesDetails:
        raise EnergyEstimateUnavailable("A basic profile and explicit energy preferences are required.")
    profile = validate_profile(profile.age, profile.height_cm, profile.weight_kg, profile.timezone)
    preferences = validate_energy_preferences(preferences.equation_sex, preferences.activity_category,
                                               preferences.context)
    if profile.age < 19:
        raise EnergyEstimateUnavailable("This adult energy method requires age 19 or older.")
    if preferences.context != "general_adult":
        raise EnergyEstimateUnavailable("This calculation context is outside the supported adult scope.")
    if preferences.equation_sex == "unsure" or preferences.activity_category == "unsure":
        raise EnergyEstimateUnavailable("Explicit equation sex and whole-day activity choices are required.")
    constant, age_factor, height_factor, weight_factor = _ADULT_EER_COEFFICIENTS[
        preferences.equation_sex, preferences.activity_category
    ]
    energy = math.fsum((constant, age_factor * profile.age, height_factor * profile.height_cm,
                        weight_factor * profile.weight_kg))
    if not math.isfinite(energy) or energy <= 0:
        raise EnergyEstimateUnavailable("The supplied profile does not produce a supported energy estimate.")
    return AdultEnergyEstimate(energy, ENERGY_METHOD_VERSION, preferences.equation_sex,
                               preferences.activity_category)
