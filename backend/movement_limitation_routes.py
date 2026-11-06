"""Guarded one-field movement limitation self-report API."""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from backend.guards import AuthenticatedAccount, require_same_origin
from backend.movement_limitations import read_movement_limitations, save_movement_limitations
from backend.profiles import read_profile
from backend.request_validation import read_json
from backend.schemas import MovementLimitationsInput, MovementLimitationsResponse
from backend.services.movement_limitations import validate_movement_limitations

router = APIRouter(prefix="/api/movement-limitations")
MAX_MOVEMENT_LIMITATIONS_BYTES = 2048


@router.get("", response_model=MovementLimitationsResponse)
async def get_movement_limitations(identity: AuthenticatedAccount):
    details = await run_in_threadpool(read_movement_limitations, identity.user_id)
    if details is None:
        raise HTTPException(404, "Choose your movement limitation status first.")
    return MovementLimitationsResponse(status=details.status)


@router.put("", response_model=MovementLimitationsResponse,
            dependencies=[Depends(require_same_origin)])
async def update_movement_limitations(request: Request, identity: AuthenticatedAccount):
    values = await read_json(request, MAX_MOVEMENT_LIMITATIONS_BYTES)
    try:
        incoming = MovementLimitationsInput.model_validate(values)
    except ValidationError:
        raise HTTPException(422, "Choose one movement limitation status.") from None
    details = validate_movement_limitations(incoming.status)
    if await run_in_threadpool(read_profile, identity.user_id) is None:
        raise HTTPException(409, "Save your basic profile first.")
    saved = await run_in_threadpool(save_movement_limitations, identity.user_id, details)
    return MovementLimitationsResponse(status=saved.status)
