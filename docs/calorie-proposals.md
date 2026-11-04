# Calorie Proposal Storage Boundary

Decision recorded 2026-11-05. A proposal is an immutable, private record of one
explicit calorie-adjustment request and the exact saved inputs used to calculate
it. It is **pending review**, not an active daily target, meal prescription, or
plan version. The existing experimental preview policy and DRI method remain
unchanged; see [preview limits](calorie-preview.md) and
[maintenance method](energy-estimation.md).

## Create boundary

- Only the signed-in owner may request a draft. A future HTTP endpoint must take
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
