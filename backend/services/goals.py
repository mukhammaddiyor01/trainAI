"""Validate recorded weight goals without prescribing a plan or deadline."""

from dataclasses import dataclass
import math


class InvalidGoal(ValueError):
    """A goal is incomplete or inconsistent with its starting weight."""


@dataclass(frozen=True)
class GoalDetails:
    direction: str
    starting_weight_kg: float
    target_weight_kg: float | None


def supported_weight(value: float, name: str) -> float:
    if type(value) not in (int, float) or not 20 <= value <= 500 or not math.isfinite(value):
        raise InvalidGoal(f"Enter a {name} weight from 20 to 500 kg.")
    return float(value)


def validate_goal(direction: str, starting_weight_kg: float,
                  target_weight_kg: float | None) -> GoalDetails:
    if direction not in ("gain", "lose", "maintain"):
        raise InvalidGoal("Choose gain, lose, or maintain as your goal.")
    starting = supported_weight(starting_weight_kg, "starting")
    if direction == "maintain":
        if target_weight_kg is not None:
            raise InvalidGoal("A maintenance goal does not use a target weight.")
        return GoalDetails(direction, starting, None)
    if target_weight_kg is None:
        raise InvalidGoal("Enter a target weight for a gain or loss goal.")
    target = supported_weight(target_weight_kg, "target")
    if direction == "gain" and target <= starting:
        raise InvalidGoal("A gain target must be above your starting weight.")
    if direction == "lose" and target >= starting:
        raise InvalidGoal("A loss target must be below your starting weight.")
    return GoalDetails(direction, starting, target)
