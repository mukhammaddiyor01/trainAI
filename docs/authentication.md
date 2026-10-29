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
tokens belong only in a browser's HttpOnly session cookie. HTTP routes and browser pages are implemented and verified separately.

Verified dependency: argon2-cffi 25.1.0.

Sources: [argon2-cffi hashing](https://argon2-cffi.readthedocs.io/en/stable/howto.html),
[OWASP authentication guidance](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html),
[OWASP session guidance](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html).

## Persistent sessions

Registration returns a plain immutable identity after the transaction commits.
Login uses one generic error for unknown usernames and wrong passwords, verifies
Argon2 outside the read transaction, and rehashes passwords when parameters change.
Successful login creates a fresh token and revokes the previous browser token.
Identity lookups join sessions to users and enforce expiry on the server. Logout
revokes only the supplied token and is idempotent. No browser user_id establishes
identity. These operations are verified against the disposable PostgreSQL cluster.

## HTTP contract

POST /auth/register and POST /auth/login accept only username/password JSON,
with a 2048-byte streamed body limit. Every state-changing authentication request
requires an Origin header matching the local page exactly; missing or cross-origin
requests are rejected. Registration does not implicitly log in. Login sets a fresh
HttpOnly, SameSite=Strict, host-only cookie, valid for 24 hours; Secure is enabled
under HTTPS. HTTP cookies are only intended for loopback development.

GET /auth/me derives identity exclusively from a valid session cookie. POST
/auth/logout revokes it. Raw tokens and passwords never appear in response bodies
or validation errors. Persistence failures return a generic 503. Hashing and database
work run in worker threads; at most two registration/login operations run at once.
The web health endpoint and public page do not require database availability.

## Browser experience

/login and /register use labeled responsive forms, password-manager autocomplete,
local JavaScript, live status feedback, duplicate-submit protection, and a
15-second request timeout. Password fields are cleared before a request is sent.
No credentials are placed in query strings, browser storage, or error messages.
/account resolves its identity from the session token, redirects anonymous
visitors, and provides sign-out. Fitness onboarding remains a later increment.

Registration, sign-in, invalid-password feedback, private account access, and
logout were verified in a browser using the disposable database runner. Desktop
and mobile layouts were inspected. The configured real database was migrated
explicitly, but synthetic browser accounts were not added to it.
