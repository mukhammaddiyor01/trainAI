"""Strict owner-scoped food-preference API; no plan or food-safety claims."""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from backend.food_preferences import read_food_preferences, save_food_preferences
from backend.guards import AuthenticatedAccount, require_same_origin
from backend.profiles import read_profile
from backend.request_validation import read_json
from backend.schemas import FoodPreferencesInput, FoodPreferencesResponse
from backend.services.food_preferences import validate_food_preferences

router = APIRouter(prefix="/api/food-preferences")
MAX_FOOD_PREFERENCE_BYTES = 8192


def public_food_preferences(details) -> FoodPreferencesResponse:
    return FoodPreferencesResponse(diet=details.diet, allergy_status=details.allergy_status,
                                   allergies=list(details.allergies), budget_level=details.budget_level,
                                   prep_minutes=details.prep_minutes, meal_times=list(details.meal_times))


@router.get("", response_model=FoodPreferencesResponse)
async def get_food_preferences(identity: AuthenticatedAccount):
    details = await run_in_threadpool(read_food_preferences, identity.user_id)
    if details is None:
        raise HTTPException(404, "Save your food preferences first.")
    return public_food_preferences(details)


@router.put("", response_model=FoodPreferencesResponse, dependencies=[Depends(require_same_origin)])
async def update_food_preferences(request: Request, identity: AuthenticatedAccount):
    values = await read_json(request, MAX_FOOD_PREFERENCE_BYTES)
    try:
        incoming = FoodPreferencesInput.model_validate(values)
    except ValidationError:
        raise HTTPException(422, "Check the diet, allergy status, allergy names, budget, preparation, and meal time fields.") from None
    details = validate_food_preferences(**incoming.model_dump())
    if await run_in_threadpool(read_profile, identity.user_id) is None:
        raise HTTPException(409, "Save your basic profile before food preferences.")
    saved = await run_in_threadpool(save_food_preferences, identity.user_id, details)
    return public_food_preferences(saved)
