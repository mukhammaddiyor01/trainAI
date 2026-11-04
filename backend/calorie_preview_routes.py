"""Guarded explicit-request preview; no target/plan is stored or activated."""

from dataclasses import asdict
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from backend.calorie_previews import read_calorie_preview_inputs
from backend.guards import AuthenticatedAccount, require_same_origin
from backend.request_validation import read_json
from backend.schemas import CaloriePreviewInput, CaloriePreviewResponse
from backend.services.calorie_preview import CaloriePreviewUnavailable, InvalidCalorieAdjustment, preview_calorie_adjustment
from backend.services.energy_estimation import EnergyEstimateUnavailable

router = APIRouter(prefix="/api/calorie-preview")
MAX_CALORIE_PREVIEW_BYTES = 2048


@router.post("", response_model=CaloriePreviewResponse, dependencies=[Depends(require_same_origin)])
async def get_calorie_preview(request: Request, identity: AuthenticatedAccount):
    values = await read_json(request, MAX_CALORIE_PREVIEW_BYTES)
    try:
        incoming = CaloriePreviewInput.model_validate(values)
    except ValidationError:
        raise HTTPException(422, "Check the requested whole-number calorie adjustment.") from None
    inputs = await run_in_threadpool(read_calorie_preview_inputs, identity.user_id)
    if inputs is None:
        raise HTTPException(404, "Save your basic profile, energy preferences, and weight goal first.")
    try:
        preview = preview_calorie_adjustment(*inputs, incoming.adjustment_kcal)
    except InvalidCalorieAdjustment as error:
        raise HTTPException(422, str(error)) from None
    except (CaloriePreviewUnavailable, EnergyEstimateUnavailable) as error:
        raise HTTPException(409, str(error)) from None
    return CaloriePreviewResponse(**asdict(preview))
