"""Bounded goal requests derive ownership and starting weight on the server."""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from backend.goals import read_goal, save_goal
from backend.guards import AuthenticatedAccount, require_same_origin
from backend.request_validation import read_json
from backend.schemas import GoalInput, GoalResponse

router = APIRouter(prefix="/api/goal")
MAX_GOAL_BYTES = 2048


def public_goal(details) -> GoalResponse:
    return GoalResponse(direction=details.direction, starting_weight_kg=details.starting_weight_kg,
                        target_weight_kg=details.target_weight_kg)


@router.get("", response_model=GoalResponse)
async def get_goal(identity: AuthenticatedAccount):
    details = await run_in_threadpool(read_goal, identity.user_id)
    if details is None:
        raise HTTPException(404, "Choose a goal after saving your basic profile.")
    return public_goal(details)


@router.put("", response_model=GoalResponse, dependencies=[Depends(require_same_origin)])
async def update_goal(request: Request, identity: AuthenticatedAccount):
    values = await read_json(request, MAX_GOAL_BYTES)
    try:
        incoming = GoalInput.model_validate(values)
    except ValidationError:
        raise HTTPException(422, "Check the goal direction and target weight fields.") from None
    details = await run_in_threadpool(save_goal, identity.user_id, incoming.direction, incoming.target_weight_kg)
    return public_goal(details)
