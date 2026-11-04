# Calorie Proposal Storage Boundary

Decision recorded 2026-11-05. A proposal is an immutable, private record of one
explicit calorie-adjustment request and the exact saved inputs used to calculate
it. It is **pending review**, not an active daily target, meal prescription, or
plan version. The existing experimental preview policy and DRI method remain
unchanged; see [preview limits](calorie-preview.md) and
[maintenance method](energy-estimation.md).

## Create boundary

- Only the signed-in owner may request a draft. The HTTP endpoint takes
  the adjustment magnitude alone, with exact Origin, strict JSON, and request
  limits. Browser-supplied owner, goal, maintenance, versions, or status cannot
  supply proposal data.
- Lock the owner's current profile row, then read the owner goal and energy
  preferences within that transaction. Revalidate all three plain values and
  recompute the preview on the server before inserting anything. A missing or
  out-of-scope input leaves no proposal behind.
- Keep a server-generated proposal UUID and creation time. Store the exact
  calculation-relevant profile age, height, and weight; saved goal direction,
  starting weight, and target; energy equation choices; requested magnitude;
  unrounded maintenance and preview; signed change; and method/policy versions.
  The profile time zone is not a calculation input and is not copied.
- New rows are pending only. They do not alter the current goal, energy choices,
  profile, or any active target. Existing proposals are retained when inputs
  change. No proposal is generated from a read-only preview request.

## Implemented storage and API

Migration 0007 adds `calorie_proposals` without changing existing tables or
backfilling users. PostgreSQL permits only pending status and checks owner foreign
keys, supported goal shape, choice labels, bounded magnitude, signed direction,
floor, and pinned method/policy versions. The storage function locks the profile
before joining and locking the owner's goal and energy rows. It validates the
plain inputs and recomputes the preview inside that transaction, then inserts
an immutable snapshot. An invalid request leaves no row.

`POST /api/calorie-proposals` accepts only `adjustment_kcal` in a 2048-byte
JSON body and requires the account session and exact Origin. It returns 201 and
nine allowlisted fields: proposal ID, creation time, pending status, maintenance,
signed change, preview, goal direction, energy method, and policy version.
`GET /api/calorie-proposals/{proposal_id}` reads only the signed-in owner's row;
another owner's ID and nonexistent IDs both return 404. Missing saved inputs
return 404, unsupported current scope 409, and invalid magnitudes 422. Existing
rate, body-time, response-size, and browser privacy limits apply. The API does
not expose source snapshots or approve a target. Repeating a POST creates a new
pending proposal with a new ID; no idempotent approval has been implemented.

Two schema checks, three storage checks, and three API checks passed in disposable
PostgreSQL. The complete isolated suite passed 181 tests, none skipped, including
migration round trips. The configured database was checked at 0006 with no table
conflict, then explicitly upgraded to 0007; no real profile or proposal rows were
read or written during verification. Dependencies and UI were unchanged. A
browser control for saving/reviewing proposals was added in a later increment.

## Browser save and review — 2026-11-05

After a successful explicit `/calorie-preview` calculation, the user can choose
**Save pending proposal**. This sends only the requested magnitude to the guarded
create API. The server locks and revalidates current inputs and recomputes; a
changed or out-of-scope input can reject the save. The button is unavailable
before a preview and the result is cleared when the amount changes. A successful
save opens `/calorie-proposals/{proposal_id}`, a private, owner-scoped page that
renders the saved snapshot on later visits. Another owner's or missing ID yields
the same 404 page; anonymous visits redirect to login. The page shows pending
status, saved time, rounded displayed values, and calculation versions. It does
not expose the source snapshot fields or offer approval. The address must be kept
to revisit the proposal at this checkpoint; a browsable list followed later.

Two focused private-page tests and two preview-page checks passed. A synthetic
disposable browser flow verified explicit preview, save, redirect, reload, mobile
width without overflow, and no console warnings/errors. The full isolated suite
passed 183 tests, none skipped, with migration round trips. No schema, dependency,
configured user data, or active target was changed by this browser increment.

## Owner-only proposal list — 2026-11-05

`GET /api/calorie-proposals` returns at most 20 saved pending proposals per page,
ordered newest first by creation time and UUID. Its explicit response schema
includes only the same nine allowlisted proposal fields and an optional
`next_before` UUID. `before` must be a single valid UUID belonging to the signed-in
owner; a foreign or nonexistent cursor receives 404, while malformed, duplicate,
or unexpected query fields receive 422. The storage query loads at most 21 owner
rows and uses the owner's cursor timestamp/UUID to continue without offset.

The authenticated `/calorie-proposals` page presents this bounded list with
**View older proposals**, an honest empty state, and detail links. Account,
preview, and detail pages link to it. It also rejects foreign/missing cursors
without displaying another user's data. The list is a discovery aid for saved
pending snapshots, not approval or a timeline of active plans.

Four focused storage/API checks and two page checks passed independently. A
synthetic browser flow verified empty and populated states, navigation, desktop
and 390 px mobile widths without overflow, and no console warnings/errors. The
full isolated PostgreSQL suite passed 187 tests, none skipped. No migration,
dependency, configured user record, or active target changed.

## Future approval boundary

Approval is a separate feature and requires an explicit user action. It must
lock the proposal, owner's source rows, and the active-plan pointer in a defined
order, recompute under the stored policy/method, and compare source snapshots.
Any changed input or superseding active plan makes an approval stale. Retries
must be idempotent; concurrent approvals must leave at most one active plan per
owner, enforced by PostgreSQL as well as service logic. Old plan versions must
be preserved. A pending proposal cannot be treated as an approved plan until
those controls and their tests exist.

The exact offset/floor/BMI bounds are authored product scope, not clinical
recommendations. Proposal storage does not establish nutritional adequacy,
predict a completion date, or select foods/workouts. No real user records belong
in tests, logs, source control, or external services.
