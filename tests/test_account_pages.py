"""Public authentication pages and anonymous account boundaries."""

import unittest

from fastapi.testclient import TestClient

from backend.main import create_app


class AccountPageTests(unittest.TestCase):
    def setUp(self):
        self.client = self.enterContext(TestClient(create_app(), base_url="http://127.0.0.1"))

    def test_public_forms_use_post_and_password_autocomplete(self):
        for path, autocomplete in [("/login", "current-password"), ("/register", "new-password")]:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertIn('method="post"', response.text)
                self.assertIn(f'autocomplete="{autocomplete}"', response.text)
                self.assertIn('type="password"', response.text)
                self.assertIn('role="status"', response.text)

    def test_anonymous_account_page_redirects_to_sign_in(self):
        response = self.client.get("/account", follow_redirects=False)
        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.headers["location"], "/login")

    def test_local_auth_assets_are_served(self):
        for path in ["/static/css/auth.css", "/static/js/auth.js"]:
            self.assertEqual(self.client.get(path).status_code, 200)


    def test_profile_page_redirects_anonymous_visitors(self):
        response = self.client.get("/profile", follow_redirects=False)
        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.headers["location"], "/login")
