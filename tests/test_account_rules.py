"""Authentication rules and cryptographic boundaries without a database."""

import unittest

from backend.passwords import hash_password, verify_password
from backend.services.accounts import InvalidAccountInput, normalize_username, validate_password
from backend.session_tokens import new_session_token, token_digest


class AccountRuleTests(unittest.TestCase):
    def test_username_is_canonical_and_rejects_unsupported_input(self):
        self.assertEqual(normalize_username("  Test_User  "), "test_user")
        for value in ["ab", "x" * 33, "person@example.com", "person/name", "müller"]:
            with self.subTest(value=value), self.assertRaises(InvalidAccountInput):
                normalize_username(value)

    def test_password_bounds_and_whitespace_are_explicit(self):
        validate_password("a" * 8)
        validate_password("a" * 128)
        validate_password("  synthetic passphrase  ")
        for value in ["a" * 7, "a" * 129, "null\x00inside-password"]:
            with self.subTest(length=len(value)), self.assertRaises(InvalidAccountInput):
                validate_password(value)

    def test_argon2_hashes_are_salted_and_wrong_password_fails(self):
        password = "synthetic test passphrase"
        first, second = hash_password(password), hash_password(password)
        self.assertNotEqual(first, second)
        self.assertTrue(first.startswith("$argon2id$"))
        self.assertTrue(verify_password(first, password))
        self.assertFalse(verify_password(first, "a different synthetic passphrase"))
        self.assertFalse(verify_password("broken-hash", password))
        self.assertFalse(verify_password(first, "short"))

    def test_session_tokens_are_random_and_only_digests_are_persistable(self):
        first, second = new_session_token(), new_session_token()
        self.assertNotEqual(first, second)
        digest = token_digest(first)
        self.assertEqual(len(digest), 64)
        self.assertNotEqual(digest, first)
        self.assertEqual(token_digest(first), digest)
        for invalid in [None, "", "x" * 42, "x" * 44, "/" * 43, "é" * 43]:
            self.assertIsNone(token_digest(invalid))


if __name__ == "__main__":
    unittest.main()
