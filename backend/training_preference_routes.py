"""Bounded preference API with shared origin and server-side identity guards."""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from backend.guards import AuthenticatedAccount, require_same_origin
from backend.profiles import read_profile
from backend.request_validation import read_json
from backend.schemas import TrainingPreferencesInput, TrainingPreferencesResponse
from backend.services.training_preferences import validate_training_preferences
from backend.training_preferences import read_training_preferences, save_training_preferences

router = APIRouter(prefix="/api/training-preferences")
MAX_TRAINING_PREFERENCE_BYTES = 4096


def public_training_preferences(details) -> TrainingPreferencesResponse:
    return TrainingPreferencesResponse(experience=details.experience, activity=details.activity,
                                       equipment=list(details.equipment), weekdays=list(details.weekdays),
                                       session_minutes=details.session_minutes)


@router.get("", response_model=TrainingPreferencesResponse)
async def get_training_preferences(identity: AuthenticatedAccount):
    details = await run_in_threadpool(read_training_preferences, identity.user_id)
    if details is None:
        raise HTTPException(404, "Save your training preferences first.")
    return public_training_preferences(details)


@router.put("", response_model=TrainingPreferencesResponse, dependencies=[Depends(require_same_origin)])
async def update_training_preferences(request: Request, identity: AuthenticatedAccount):
    values = await read_json(request, MAX_TRAINING_PREFERENCE_BYTES)
    try:
        incoming = TrainingPreferencesInput.model_validate(values)
    except ValidationError:
        raise HTTPException(422, "Check the training experience, activity, equipment, weekdays, and duration fields.") from None
    details = validate_training_preferences(**incoming.model_dump())
    if await run_in_threadpool(read_profile, identity.user_id) is None:
        raise HTTPException(409, "Save your basic profile before training preferences.")
    saved = await run_in_threadpool(save_training_preferences, identity.user_id, details)
    return public_training_preferences(saved)
