"""Bounded read-only weekly review of the signed-in owner's observations."""

from fastapi import APIRouter, HTTPException, Request
from starlette.concurrency import run_in_threadpool

from backend.guards import AuthenticatedAccount
from backend.schemas import WeightEntryResponse, WeeklyWeightResponse, WeightReviewResponse
from backend.weight_entries import read_weight_review


router = APIRouter(prefix="/api/weight-review")


@router.get("", response_model=WeightReviewResponse)
async def get_weight_review(request: Request, identity: AuthenticatedAccount):
    if request.query_params:
        raise HTTPException(422, "Unexpected query fields.")
    review = await run_in_threadpool(read_weight_review, identity.user_id)
    if review is None:
        raise HTTPException(404, "Save a basic profile before reviewing weight.")
    return WeightReviewResponse(weeks=[WeeklyWeightResponse(
        week_start=week.week_start, week_end=week.week_end,
        observed_dates=week.observed_dates,
        first=WeightEntryResponse(local_date=week.first.local_date,
                                  weight_kg=week.first.weight_kg) if week.first else None,
        last=WeightEntryResponse(local_date=week.last.local_date,
                                 weight_kg=week.last.weight_kg) if week.last else None,
        observed_change_kg=week.observed_change_kg,
    ) for week in review])
