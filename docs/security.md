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
| Credential bodies | 2048 bytes, including streamed/chunked bodies |
| Body arrival | 10 seconds total, then 408 |
| Metadata | 64 headers, 16 KiB header bytes, 4096-byte request target |
| JSON API response | 64 KiB on /auth/ and /api/; oversized responses fail before any body is exposed |
| API requests | 120 per client address per rolling 60 seconds |
| Credential requests | 30 per client address per rolling 60 seconds |
| Login attempts | 8 per normalized username per rolling 60 seconds |
| Limiter state | 4096 fingerprint buckets per limiter, expired entries removed, capacity fails closed |
| Password work | Two simultaneous registration/login operations |
| PostgreSQL | 5-second connection/statement bounds, 2-second lock bound |
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
