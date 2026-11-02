"""Strict owner-scoped energy preference collection without inferred choices."""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from backend.energy_preferences import read_energy_preferences, save_energy_preferences
from backend.guards import AuthenticatedAccount, require_same_origin
from backend.profiles import read_profile
from backend.request_validation import read_json
from backend.schemas import EnergyPreferencesInput, EnergyPreferencesResponse
from backend.services.energy_preferences import validate_energy_preferences

router = APIRouter(prefix="/api/energy-preferences")
MAX_ENERGY_PREFERENCE_BYTES = 2048


def public_energy_preferences(details) -> EnergyPreferencesResponse:
    return EnergyPreferencesResponse(equation_sex=details.equation_sex,
                                     activity_category=details.activity_category, context=details.context)


@router.get("", response_model=EnergyPreferencesResponse)
async def get_energy_preferences(identity: AuthenticatedAccount):
    details = await run_in_threadpool(read_energy_preferences, identity.user_id)
    if details is None:
        raise HTTPException(404, "Save your energy preferences first.")
    return public_energy_preferences(details)


@router.put("", response_model=EnergyPreferencesResponse, dependencies=[Depends(require_same_origin)])
async def update_energy_preferences(request: Request, identity: AuthenticatedAccount):
    values = await read_json(request, MAX_ENERGY_PREFERENCE_BYTES)
    try:
        incoming = EnergyPreferencesInput.model_validate(values)
    except ValidationError:
        raise HTTPException(422, "Check the equation sex, whole-day activity category, and calculation context.") from None
    details = validate_energy_preferences(**incoming.model_dump())
    if await run_in_threadpool(read_profile, identity.user_id) is None:
        raise HTTPException(409, "Save your basic profile before energy preferences.")
    saved = await run_in_threadpool(save_energy_preferences, identity.user_id, details)
    return public_energy_preferences(saved)
