"""Web-shell boundaries, honest availability, and intended public assets."""

import unittest

from fastapi.testclient import TestClient

from backend.main import create_app


class WebShellTests(unittest.TestCase):
    def setUp(self):
        self.client = self.enterContext(
            TestClient(create_app(), base_url="http://127.0.0.1")
        )

    def test_home_renders_and_reports_unavailable_features(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn('<html lang="en">', response.text)
        self.assertIn("Accounts and planning are coming next", response.text)
        self.assertIn("Not connected", response.text)
        self.assertNotIn("<form", response.text)

    def test_health_does_not_claim_database_or_model_readiness(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "status": "ok", "scope": "web", "ai": "not_configured",
        })

    def test_stylesheet_is_served(self):
        response = self.client.get("/static/css/styles.css")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/css", response.headers["content-type"])

    def test_private_project_files_are_not_public_assets(self):
        for path in ["/AGENTS.md", "/.env", "/.git/config", "/backend/main.py",
                     "/static/../AGENTS.md", "/static/%2e%2e/AGENTS.md",
                     "/static/%2e%2e/%2e%2e/AGENTS.md"]:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 404)

    def test_unexpected_hosts_are_rejected(self):
        response = self.client.get("/", headers={"host": "untrusted.example"})
        self.assertEqual(response.status_code, 400)

    def test_browser_policies_apply_to_success_and_error_responses(self):
        for path in ["/", "/health", "/missing"]:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.headers["cache-control"], "no-store")
                self.assertEqual(response.headers["x-content-type-options"], "nosniff")
                self.assertIn("frame-ancestors 'none'", response.headers["content-security-policy"])
                self.assertEqual(response.headers["permissions-policy"], "camera=(), microphone=()")

    def test_shell_does_not_accept_private_profile_writes(self):
        self.assertEqual(self.client.post("/").status_code, 405)
        self.assertEqual(self.client.post("/profiles", json={"user_id": 1}).status_code, 404)


if __name__ == "__main__":
    unittest.main()
