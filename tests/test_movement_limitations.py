"""An unknown movement status cannot silently become clearance for planning."""

import unittest
from dataclasses import FrozenInstanceError

from backend.services.movement_limitations import (
    InvalidMovementLimitations, validate_movement_limitations,
)


class MovementLimitationRuleTests(unittest.TestCase):
    def test_each_explicit_answer_is_preserved_without_interpretation(self):
        for status in ("unsure", "none_reported", "needs_adaptation"):
            with self.subTest(status=status):
                answer = validate_movement_limitations(status)
                self.assertEqual(answer.status, status)
                with self.assertRaises(FrozenInstanceError):
                    answer.status = "none_reported"

    def test_missing_coercible_and_forged_answers_fail_closed(self):
        for answer in (None, "", "Unknown", "no", "cleared", True, 0, ["none_reported"]):
            with self.subTest(answer=answer), self.assertRaises(InvalidMovementLimitations):
                validate_movement_limitations(answer)
