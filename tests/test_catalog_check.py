"""The explicit catalog check is offline, read-only, and honest about readiness."""

from contextlib import redirect_stdout
from io import StringIO
import os
import unittest
from unittest.mock import patch

from backend.check_catalogs import main
from backend.services.catalogs import InvalidCatalog


class CatalogCheckTests(unittest.TestCase):
    def test_operator_check_needs_no_network_or_database_and_does_not_claim_food_readiness(self):
        output = StringIO()
        with patch.dict(os.environ,{"DATABASE_URL":"must-not-be-read"}), \
                patch("socket.socket",side_effect=AssertionError("Network access is not allowed")), \
                redirect_stdout(output):
            self.assertEqual(main(),0)
        self.assertIn("Exercise metadata records: 6",output.getvalue())
        self.assertIn("Food nutrient records: 4",output.getvalue())
        self.assertIn("Food selection: unavailable",output.getvalue())
        self.assertIn("Reviewed allergy-name groups: 9",output.getvalue())
        self.assertIn("Reviewed allergy terms: 15",output.getvalue())
        self.assertIn("Food composition reviews pending: 4",output.getvalue())
        self.assertIn("fda-major-terms-2026-11-02-v1",output.getvalue())

    def test_invalid_evidence_returns_failure_without_echoing_imported_text(self):
        output = StringIO()
        with patch("backend.check_catalogs.load_exercises",side_effect=InvalidCatalog("untrusted source marker")), redirect_stdout(output):
            self.assertEqual(main(),1)
        self.assertIn("Catalog verification failed",output.getvalue())
        self.assertNotIn("untrusted source marker",output.getvalue())

    def test_ambiguous_allergy_registry_fails_the_operator_check_safely(self):
        output = StringIO()
        groups = (("milk",("milk",)),("soy",("milk",)))
        with patch("backend.services.allergens.ALLERGEN_GROUPS",groups), redirect_stdout(output):
            self.assertEqual(main(),1)
        self.assertIn("Catalog verification failed",output.getvalue())
        self.assertNotIn("Reviewed allergy terms",output.getvalue())
