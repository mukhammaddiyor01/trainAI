"""Owner-scoped, atomic food-preference storage returning plain values."""

from uuid import UUID
from sqlalchemy.dialects.postgresql import insert

from backend.database import session_scope
from backend.models import FoodPreferences
from backend.services.food_preferences import FoodPreferencesDetails, validate_food_preferences


def read_food_preferences(user_id: UUID) -> FoodPreferencesDetails | None:
    with session_scope() as session:
        record = session.get(FoodPreferences, user_id)
        if record is None:
            return None
        times = [f"{minute // 60:02d}:{minute % 60:02d}" for minute in record.meal_minutes]
        return validate_food_preferences(record.diet, record.allergy_status, record.allergies,
                                          record.budget_level, record.prep_minutes, times)


def save_food_preferences(user_id: UUID, details: FoodPreferencesDetails) -> FoodPreferencesDetails:
    details = validate_food_preferences(details.diet, details.allergy_status, details.allergies,
                                         details.budget_level, details.prep_minutes, details.meal_times)
    minutes = [int(time[:2]) * 60 + int(time[3:]) for time in details.meal_times]
    values = dict(diet=details.diet, allergy_status=details.allergy_status,
                  allergies=list(details.allergies), budget_level=details.budget_level,
                  prep_minutes=details.prep_minutes, meal_minutes=minutes)
    statement = insert(FoodPreferences).values(user_id=user_id, **values).on_conflict_do_update(
        index_elements=[FoodPreferences.user_id], set_=values,
    )
    with session_scope() as session:
        session.execute(statement)
    return details
