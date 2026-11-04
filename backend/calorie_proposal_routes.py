"""Guarded pending proposal creation and owner-only snapshot reads."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from backend.calorie_proposals import CalorieProposalInputsRequired, PendingCalorieProposal, ProposalCursorNotFound, create_calorie_proposal, list_calorie_proposals, read_calorie_proposal
from backend.guards import AuthenticatedAccount, require_same_origin
from backend.request_validation import read_json
from backend.schemas import CaloriePreviewInput, CalorieProposalListResponse, CalorieProposalResponse
from backend.services.calorie_preview import CaloriePreviewUnavailable, InvalidCalorieAdjustment
from backend.services.energy_estimation import EnergyEstimateUnavailable

router = APIRouter(prefix="/api/calorie-proposals")
MAX_PROPOSAL_BYTES = 2048


def _response(details: PendingCalorieProposal) -> CalorieProposalResponse:
    return CalorieProposalResponse(
        proposal_id=details.id, created_at=details.created_at, status=details.status,
        maintenance_kcal_per_day=details.maintenance_kcal_per_day,
        adjustment_kcal_per_day=details.signed_adjustment_kcal,
        preview_kcal_per_day=details.preview_kcal_per_day,
        goal_direction=details.goal_direction,
        energy_method_version=details.energy_method_version,
        policy_version=details.policy_version,
    )


def parse_proposal_cursor(request: Request) -> UUID | None:
    if not request.query_params:
        return None
    if set(request.query_params) != {"before"} or len(request.query_params.getlist("before")) != 1:
        raise HTTPException(422, "Use one valid proposal cursor.")
    try:
        return UUID(request.query_params["before"])
    except (ValueError, AttributeError):
        raise HTTPException(422, "Use one valid proposal cursor.") from None


@router.post("", response_model=CalorieProposalResponse, status_code=201,
             dependencies=[Depends(require_same_origin)])
async def create_proposal(request: Request, identity: AuthenticatedAccount):
    values = await read_json(request, MAX_PROPOSAL_BYTES)
    try:
        incoming = CaloriePreviewInput.model_validate(values)
    except ValidationError:
        raise HTTPException(422, "Check the requested whole-number calorie adjustment.") from None
    try:
        details = await run_in_threadpool(create_calorie_proposal, identity.user_id, incoming.adjustment_kcal)
    except CalorieProposalInputsRequired as error:
        raise HTTPException(404, str(error)) from None
    except InvalidCalorieAdjustment as error:
        raise HTTPException(422, str(error)) from None
    except (CaloriePreviewUnavailable, EnergyEstimateUnavailable) as error:
        raise HTTPException(409, str(error)) from None
    return _response(details)


@router.get("", response_model=CalorieProposalListResponse)
async def list_proposals(request: Request, identity: AuthenticatedAccount):
    before = parse_proposal_cursor(request)
    try:
        page = await run_in_threadpool(list_calorie_proposals, identity.user_id, before)
    except ProposalCursorNotFound:
        raise HTTPException(404, "Proposal page not found.") from None
    return CalorieProposalListResponse(
        items=[_response(item) for item in page.items], next_before=page.next_before,
    )


@router.get("/{proposal_id}", response_model=CalorieProposalResponse)
async def get_proposal(proposal_id: UUID, identity: AuthenticatedAccount):
    details = await run_in_threadpool(read_calorie_proposal, identity.user_id, proposal_id)
    if details is None:
        raise HTTPException(404, "Proposal not found.")
    return _response(details)
