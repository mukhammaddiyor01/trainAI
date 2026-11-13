"""Guarded API for user-reported sleep duration on an owner-local date."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from backend.guards import AuthenticatedAccount, require_same_origin
from backend.request_validation import read_json
from backend.schemas import SleepEntryInput, SleepEntryListResponse, SleepEntryResponse
from backend.services.sleep_entries import SleepEntryDetails
from backend.sleep_entries import list_recent_sleep_entries, save_sleep_entry


router = APIRouter(prefix="/api/sleep-entries")
MAX_SLEEP_ENTRY_BYTES = 2048


@router.get("", response_model=SleepEntryListResponse)
async def list_sleep_entries(request: Request, identity: AuthenticatedAccount):
    if request.query_params:
        raise HTTPException(422, "Unexpected query fields.")
    entries = await run_in_threadpool(list_recent_sleep_entries, identity.user_id)
    return SleepEntryListResponse(items=[
        SleepEntryResponse(local_date=entry.local_date, sleep_minutes=entry.sleep_minutes)
        for entry in entries
    ])


@router.put("", response_model=SleepEntryResponse,
            dependencies=[Depends(require_same_origin)])
async def update_sleep_entry(request: Request, identity: AuthenticatedAccount):
    if request.query_params:
        raise HTTPException(422, "Unexpected query fields.")
    values = await read_json(request, MAX_SLEEP_ENTRY_BYTES)
    try:
        incoming = SleepEntryInput.model_validate(values)
    except ValidationError:
        raise HTTPException(422, "Enter a valid date and sleep duration.") from None
    saved = await run_in_threadpool(
        save_sleep_entry, identity.user_id,
        SleepEntryDetails(date.fromisoformat(incoming.local_date), incoming.sleep_minutes),
    )
    return SleepEntryResponse(local_date=saved.local_date, sleep_minutes=saved.sleep_minutes)
