"""Guarded API for explicit owner-local weight observations."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from backend.guards import AuthenticatedAccount, require_same_origin
from backend.request_validation import read_json
from backend.schemas import WeightEntryInput, WeightEntryListResponse, WeightEntryResponse
from backend.services.weight_entries import WeightEntryDetails
from backend.weight_entries import list_recent_weight_entries, save_weight_entry


router = APIRouter(prefix="/api/weight-entries")
MAX_WEIGHT_ENTRY_BYTES = 2048


@router.get("", response_model=WeightEntryListResponse)
async def list_weight_entries(request: Request, identity: AuthenticatedAccount):
    if request.query_params:
        raise HTTPException(422, "Unexpected query fields.")
    entries = await run_in_threadpool(list_recent_weight_entries, identity.user_id)
    return WeightEntryListResponse(items=[
        WeightEntryResponse(local_date=entry.local_date, weight_kg=entry.weight_kg)
        for entry in entries
    ])


@router.put("", response_model=WeightEntryResponse,
            dependencies=[Depends(require_same_origin)])
async def update_weight_entry(request: Request, identity: AuthenticatedAccount):
    if request.query_params:
        raise HTTPException(422, "Unexpected query fields.")
    values = await read_json(request, MAX_WEIGHT_ENTRY_BYTES)
    try:
        incoming = WeightEntryInput.model_validate(values)
    except ValidationError:
        raise HTTPException(422, "Enter a valid date and weight.") from None
    saved = await run_in_threadpool(
        save_weight_entry, identity.user_id,
        WeightEntryDetails(date.fromisoformat(incoming.local_date), incoming.weight_kg),
    )
    return WeightEntryResponse(local_date=saved.local_date, weight_kg=saved.weight_kg)
