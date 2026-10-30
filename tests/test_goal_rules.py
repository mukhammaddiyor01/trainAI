"""Goal rules are independent of models, HTTP, database, and internet."""

import unittest

from backend.services.goals import GoalDetails, InvalidGoal, validate_goal


class GoalRuleTests(unittest.TestCase):
    def test_gain_loss_and_maintenance_have_explicit_meaning(self):
        self.assertEqual(validate_goal("gain", 60, 75), GoalDetails("gain", 60.0, 75.0))
        self.assertEqual(validate_goal("lose", 90, 80), GoalDetails("lose", 90.0, 80.0))
        self.assertEqual(validate_goal("maintain", 70, None), GoalDetails("maintain", 70.0, None))

    def test_inconsistent_directions_and_missing_targets_are_rejected(self):
        cases = [("gain", 70, 70), ("gain", 70, 60), ("gain", 70, None),
                 ("lose", 70, 70), ("lose", 70, 80), ("lose", 70, None),
                 ("maintain", 70, 70), ("bulk", 70, 80), (None, 70, 80)]
        for values in cases:
            with self.subTest(values=values), self.assertRaises(InvalidGoal):
                validate_goal(*values)

    def test_unsupported_numeric_values_are_not_coerced(self):
        for value in [True, "75", 0, 501, float("nan"), float("inf"), 10 ** 1000]:
            with self.subTest(value_type=type(value).__name__), self.assertRaises(InvalidGoal):
                validate_goal("gain", 60, value)
        for value in [None, False, "60", 19, float("nan")]:
            with self.assertRaises(InvalidGoal):
                validate_goal("gain", value, 75)
