# Authentication

## Account rules

Use usernames rather than email addresses for the local first version. Usernames
are normalized to lowercase, contain 3–32 ASCII letters, digits, or underscores,
and are unique in PostgreSQL. Email delivery and password recovery are not
implemented. Account input rules are plain Python services.

Passwords are 15–128 characters, support spaces and Unicode, and are neither
trimmed nor normalized. Argon2id uses the maintained argon2-cffi PasswordHasher
defaults. Every hash has its own salt. Plaintext passwords never enter database
records or logs. Oversized and invalid passwords fail before hashing.

Sessions use cryptographically random 32-byte tokens. Only SHA-256 digests are
stored in PostgreSQL, with a user foreign key and a fixed 24-hour expiry. Raw
tokens belong only in a browser's HttpOnly session cookie. Routes and browser
flows will be introduced in a separate verified increment.

Verified dependency: argon2-cffi 25.1.0.

Sources: [argon2-cffi hashing](https://argon2-cffi.readthedocs.io/en/stable/howto.html),
[OWASP authentication guidance](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html),
[OWASP session guidance](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html).
