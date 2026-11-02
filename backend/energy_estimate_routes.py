"""Read-only energy estimate from the authenticated owner's current saved inputs."""

from dataclasses import asdict
from fastapi import APIRouter, HTTPException
from starlette.concurrency import run_in_threadpool

from backend.energy_preferences import read_energy_inputs
from backend.guards import AuthenticatedAccount
from backend.schemas import AdultEnergyEstimateResponse
from backend.services.energy_estimation import EnergyEstimateUnavailable, estimate_adult_energy

router = APIRouter(prefix="/api/energy-estimate")


@router.get("", response_model=AdultEnergyEstimateResponse)
async def get_energy_estimate(identity: AuthenticatedAccount):
    inputs = await run_in_threadpool(read_energy_inputs, identity.user_id)
    if inputs is None:
        raise HTTPException(404, "Save your basic profile and energy preferences first.")
    try:
        estimate = estimate_adult_energy(*inputs)
    except EnergyEstimateUnavailable as error:
        raise HTTPException(409, str(error)) from None
    return AdultEnergyEstimateResponse(**asdict(estimate))
