# Security Boundaries

## Current scope

Local, single-process development on 127.0.0.1. OAuth is deferred by the user's
choice; no third-party identity provider is configured. No fitness records are
sent to external providers. This document records implemented controls and their
limits, not a claim of complete security or a penetration test.

## Request and response pipeline

HTTP metadata limits → API request rate limit → same-origin write guard → bounded
UTF-8 JSON read → strict Pydantic input dependency → authenticated account guard
for private endpoints → ownership-scoped persistence → explicit response schema
→ JSON response-size bound → browser security headers.

The order of origin and identity dependencies can vary by endpoint, but private
operations must not run without a valid server-derived identity. Never trust a
browser user_id, role, Authorization placeholder, or forwarded address header.
Plain business services remain independent of these HTTP controls.

## Implemented limits

| Boundary | Limit / behavior |
| --- | --- |
| Food-preference bodies | 8192 bytes, strict six-field input, authenticated owner only |
| Training-preference bodies | 4096 bytes, strict five-field input, authenticated owner only |
| Basic profile bodies | 8192 bytes, strict four-field input, authenticated owner only |
| Credential bodies | 2048 bytes, including streamed/chunked bodies |
| Body arrival | 10 seconds total, then 408 |
| Metadata | 64 headers, 16 KiB header bytes, 4096-byte request target |
| JSON API response | 64 KiB on /auth/ and /api/; oversized responses fail before any body is exposed |
| API requests | 120 per client address per rolling 60 seconds |
| Credential requests | 30 per client address per rolling 60 seconds |
| Login attempts | 8 per normalized username per rolling 60 seconds |
| Limiter state | 4096 fingerprint buckets per limiter, expired entries removed, capacity fails closed |
| Password work | Two simultaneous registration/login operations |
| PostgreSQL | 10 connections maximum, 3-second pool wait, 5-second connection/statement bounds, 2-second lock bound |
| Local server launcher | 32 concurrent requests/connections, 5-second keep-alive, 16 KiB incomplete HTTP event buffer |

Throttling returns 429 with Retry-After. Use `python -m backend` so the documented
transport settings apply. Forwarded and X-Forwarded-* headers are rejected by the
local app; Uvicorn proxy-header trust and Server headers are disabled by the launcher.
Access logging is disabled so URLs cannot inadvertently disclose private query data.

## Validation and data exposure

Input models forbid unknown fields and coercion. The JSON parser rejects duplicate
keys, non-finite values, non-UTF-8 input, and compressed bodies. Passwords use
SecretStr inside schemas and Argon2id at rest. Validation errors do not return input
values. Public account responses expose only user_id and username. Failed response
validation and database errors produce generic messages, not payloads or tracebacks.

Sessions use random tokens, digest-only persistence, server-enforced expiry,
rotation at login, and revocation at logout. Cookies are HttpOnly, host-only,
SameSite=Strict, and Secure under HTTPS. Cleartext HTTP is limited to loopback
development. CSP, no-store, no-referrer, frame denial, and same-origin resource and
opener policies apply to normal and controlled error responses.

## Verification and remaining boundaries

Automated checks use synthetic data in an isolated temporary PostgreSQL cluster.
They cover malformed and ambiguous input, mass assignment attempts, identity
spoofing, session isolation/expiry/revocation, rate limits, streamed body limits,
slow body timeout, proxy spoofing, oversized streamed responses, and error redaction.

The rate limiter is local memory per process and resets on restart. Multi-worker
or public deployment requires a shared limiter and an explicit proxy/TLS policy.
OAuth/OIDC later requires a selected provider, registered callback, state/PKCE,
nonce and issuer/audience validation where applicable, and deliberate account
linking. Do not treat adding an OAuth button as completing those requirements.

Every new private model and endpoint needs ownership checks and its own bounds.
No deployment, paid security service, or claim of full security is authorized here.

Sources checked during implementation:
- [FastAPI dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [FastAPI response models](https://fastapi.tiangolo.com/tutorial/response-model/)
- [Pydantic strict mode](https://docs.pydantic.dev/latest/concepts/strict_mode/)
- [AnyIO timeouts](https://anyio.readthedocs.io/en/stable/cancellation.html)
- [OWASP REST security](https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html)

## Isolated browser-test cookies

Cookies are scoped to hosts and paths, not ports. The disposable test runner now
sets a unique TRAINAI_COOKIE_NAME for every cluster so signing in or out on port
8001 cannot overwrite the main application's cookie on port 8000. Other instances'
cookies are ignored by the guard. The default application name remains
trainai_session. An optional process-environment override is validated at startup;
invalid names fail closed. Changing the cookie name requires restarting the app.

## Dependency advisory snapshot

On 2026-10-29, pip-audit 2.10.1 audited the complete 29-package constraints.txt
set against the PyPI advisory service with --disable-pip --no-deps --strict.
It exited 0 and reported no known vulnerabilities. The JSON report is stored in
[dependency-audit.json](dependency-audit.json). Audit tooling ran in a separate
temporary environment; no application secrets or private data were supplied.
Version pins are recorded, but the installation is not yet a hash-locked supply
chain workflow. Advisory results can change after this snapshot.

## Goal and password increment — 2026-10-30

/api/goal uses the shared identity/origin guards, strict two-field input, a
2048-byte body limit, and existing API rate/time/response limits. Starting weight
and ownership come from the server. SQL constraints and profile row locks protect
goal shape and concurrent retries. Two-user and mass-assignment tests passed.
The user selected an 8-character password minimum; shared constants now keep the
service, input schema, and browser forms consistent. OAuth remains deferred.

## Weight goals — 2026-10-30

Goal input accepts only direction and optional target_weight_kg, capped at
2048 bytes. Shared auth/origin guards and API rate/time/response limits apply.
Ownership and starting weight are server-selected; SQL constraints and profile
row locks enforce consistency and stable identical-save retries. Responses contain
only direction, starting_weight_kg, and target_weight_kg. Cross-user access and
forged owner/starting-weight fields were tested.

The user's 8-character minimum decision is implemented through shared password
constants in the service, HTTP schema, and rendered forms. Argon2id, cookie/session
controls, and rate limits remain active. OAuth remains deferred.


## Training preferences — 2026-10-31

GET/PUT /api/training-preferences use server-derived identity and owner-scoped
queries. PUT requires the exact same Origin, bounded JSON, strict schemas, and
plain validation; unknown owner/role/storage fields are rejected. Responses expose
only the five named preferences. Existing rate/time/response limits apply.
Invalid saves preserve stored values. Tests cover two-user isolation, revoked
access, malformed and oversized requests, and missing-profile rejection. SQL
constraints and atomic upserts protect complete selections and concurrent retries.
OAuth remains deferred and the limiter remains single-process local memory.


## Food preferences — 2026-10-31

The food API uses the shared identity/origin guards, 8192-byte bounded parser,
strict schemas, and six-field response allowlist. Unknown owner/role/time-zone or
storage fields cannot establish identity or overwrite a different owner's row.
Existing rate/time/response budgets remain active. Reported names are private
text data; errors do not echo them and Jinja escapes them in the form. They are
not instructions, diagnoses, or verified ingredient/allergen mappings. No default
absence of allergy is inferred. Invalid updates preserve stored values. Two-user,
revocation, ambiguous/oversized JSON, and HTML-escaping checks passed. OAuth and
the single-process limiter scope are unchanged.


## Bundled catalogs — 2026-10-31

Reference records live outside frontend/static and have no new HTTP endpoints.
Catalog loading reads fixed bundled files with byte/record bounds, rejects duplicate
JSON keys, non-finite values, missing/unknown metadata, unsupported units/licenses,
and duplicate IDs. Exercise records are checked against retained source metadata;
food response snapshots are verified against SHA-256 digests and imported
identity/nutrient/unit values are compared with those responses. Source URLs are
provenance text and never fetched by the runtime. Import review used only public
records and the documented USDA DEMO_KEY; no private keys/profiles were supplied.
Operator checks work offline with database access unavailable. Incomplete food
composition/diet/allergen review blocks automatic selection; untrusted source text
is never executed or promoted into AI instructions or personalized guidance.


## Bounded allergy-name resolution — 2026-11-02

Names remain bounded plain data and use the same normalization as stored food
preferences. Resolution is exact against a versioned authored subset; it performs
no model inference, fuzzy matching, translation, or substring matching. Unknowns
are preserved and block future selection, including when other names resolve.
Names/results are neither logged nor transmitted. Offline operator checks report
only public registry counts/version and pending composition counts. Ambiguous
registry entries fail with a generic diagnostic. Existing HTTP/body/response and
owner guards remain unchanged. Recognized names do not bypass ingredient or
food-composition review, and every current nutrient seed remains blocked.
