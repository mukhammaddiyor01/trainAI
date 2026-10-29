"""Profile business rules run without HTTP, database, models, or internet."""

import unittest

from backend.services.profiles import InvalidProfile, ProfileDetails, validate_profile


class ProfileRuleTests(unittest.TestCase):
    def test_valid_metric_profile_and_explicit_time_zone(self):
        self.assertEqual(validate_profile(28, 172, 70, "Asia/Seoul"),
                         ProfileDetails(28, 172.0, 70.0, "Asia/Seoul"))
        self.assertEqual(validate_profile(18, 50, 20, "UTC").age, 18)

    def test_invalid_incomplete_and_nonfinite_values_are_rejected(self):
        valid = {"age": 28, "height_cm": 172.0, "weight_kg": 70.0, "timezone": "UTC"}
        changes = [{"age": 17}, {"age": 121}, {"age": True}, {"age": "28"},
                   {"height_cm": float("nan")}, {"height_cm": 301}, {"height_cm": True}, {"height_cm": 10 ** 1000},
                   {"weight_kg": float("inf")}, {"weight_kg": 0}, {"weight_kg": None},
                   {"timezone": "Asia/Unknown"}, {"timezone": "../../private"}, {"timezone": ""}]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(InvalidProfile):
                validate_profile(**{**valid, **change})
