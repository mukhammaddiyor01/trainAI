"""Guarded explicit approval and active calorie target reads."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from backend.calorie_targets import (CalorieProposalNotFound, CalorieTargetDetails,
                                     StaleCalorieProposal, approve_calorie_proposal,
                                     read_active_calorie_target)
from backend.guards import AuthenticatedAccount, require_same_origin
from backend.request_validation import read_json
from backend.schemas import CalorieApprovalInput, CalorieTargetResponse

router = APIRouter()
MAX_APPROVAL_BYTES = 2048


def _response(details: CalorieTargetDetails) -> CalorieTargetResponse:
    return CalorieTargetResponse(
        target_id=details.id, proposal_id=details.proposal_id, version=details.version,
        status=details.status, target_kcal_per_day=details.target_kcal_per_day,
        approved_at=details.approved_at,
    )


@router.post("/api/calorie-proposals/{proposal_id}/approve",
             response_model=CalorieTargetResponse, dependencies=[Depends(require_same_origin)])
async def approve_proposal(proposal_id: UUID, request: Request, identity: AuthenticatedAccount):
    values = await read_json(request, MAX_APPROVAL_BYTES)
    try:
        CalorieApprovalInput.model_validate(values)
    except ValidationError:
        raise HTTPException(422, "Explicit confirmation is required.") from None
    try:
        target = await run_in_threadpool(approve_calorie_proposal, identity.user_id, proposal_id)
    except CalorieProposalNotFound:
        raise HTTPException(404, "Proposal not found.") from None
    except StaleCalorieProposal as error:
        raise HTTPException(409, str(error)) from None
    return _response(target)


@router.get("/api/calorie-targets/active", response_model=CalorieTargetResponse)
async def get_active_target(identity: AuthenticatedAccount):
    target = await run_in_threadpool(read_active_calorie_target, identity.user_id)
    if target is None:
        raise HTTPException(404, "No active calorie target.")
    return _response(target)
