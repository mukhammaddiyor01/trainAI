"""Read and write only the authenticated user's bounded basic profile."""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from backend.guards import AuthenticatedAccount, require_same_origin
from backend.profiles import read_profile, save_profile
from backend.request_validation import read_json
from backend.schemas import ProfileInput, ProfileResponse
from backend.services.profiles import validate_profile

router = APIRouter(prefix="/api/profile")
MAX_PROFILE_BYTES = 8192


@router.get("", response_model=ProfileResponse)
async def get_profile(identity: AuthenticatedAccount):
    details = await run_in_threadpool(read_profile, identity.user_id)
    if details is None:
        raise HTTPException(404, "Complete your basic profile first.")
    return ProfileResponse(age=details.age, height_cm=details.height_cm,
                           weight_kg=details.weight_kg, timezone=details.timezone)


@router.put("", response_model=ProfileResponse, dependencies=[Depends(require_same_origin)])
async def update_profile(request: Request, identity: AuthenticatedAccount):
    values = await read_json(request, MAX_PROFILE_BYTES)
    try:
        incoming = ProfileInput.model_validate(values)
    except ValidationError:
        raise HTTPException(422, "Check the age, height, weight, and time zone fields.") from None
    details = validate_profile(**incoming.model_dump())
    saved = await run_in_threadpool(save_profile, identity.user_id, details)
    return ProfileResponse(age=saved.age, height_cm=saved.height_cm,
                           weight_kg=saved.weight_kg, timezone=saved.timezone)
