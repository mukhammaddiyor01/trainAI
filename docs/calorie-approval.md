# Calorie Target Approval Boundary

Reviewed 2026-11-06. This boundary activates a **calorie target version** from
one saved pending proposal after an explicit user action. It does not create a
weekly workout or meal plan, establish nutritional adequacy, or certify the
calorie amount as medically suitable. The experimental preview policy and DRI
method remain the calculation rules; see [calorie preview](calorie-preview.md).

## State and database invariants

- Proposal calculation inputs and values remain an immutable snapshot. Approval
  may change only its lifecycle metadata from pending to approved, with an
  approval timestamp. An approved proposal is never reused to create another
  version.
- Each target version belongs to one owner and one proposal. Versions increase
  monotonically per owner, starting at 1. A version is active or superseded;
  old versions are retained. PostgreSQL enforces one active version per owner
  with a partial unique index, plus unique owner/version and proposal references.
- Each proposal records the active version ID that existed when it was created,
  or null if there was none. Existing pending proposals receive null. This is
  an optimistic baseline, not a browser-supplied value. A pending proposal may
  be approved only while that baseline equals the owner's current active version.
- The target version stores the approved unrounded kcal/day value and references
  the proposal containing the exact calculation snapshot. The API and UI may
  round only for display. No food, workout, or AI output is activated here.

## One approval transaction

The signed-in owner names one proposal ID and explicitly confirms the action.
The server selects the owner from the session. Within one database transaction:

1. Lock the owner's profile row, then the owner-scoped proposal row. This is the
   same first lock used by proposal creation, goal saves, and profile edits.
2. If the proposal is already approved, return its existing version without
   changing the current active version. This is the idempotent retry path.
3. Lock the owner's goal and energy preference rows, then read the active target
   version. Check the proposal's baseline version against that active ID.
4. Revalidate the current profile, goal, and energy choices. Compare all
   calculation-relevant source fields with the proposal snapshot. Recompute the
   preview using its requested magnitude and pinned method/policy. Reject any
   changed, missing, out-of-scope, or unsupported input, or changed result.
5. Mark the previous active version superseded, create the next version as
   active, and mark the proposal approved. All writes commit together. A failure
   rolls everything back.

Profile row locking serializes approvals for one owner, including concurrent
retries and competing pending proposals. PostgreSQL uniqueness is a second line
of defense; a constraint conflict never silently activates two versions. An
approval of an older baseline fails even if its calorie number happens to match
the current target. A new proposal can be made from current inputs and version.

## HTTP and browser boundary

Approval requires a separate guarded POST with exact Origin, strict bounded
input, a server-derived owner, an allowlisted response, and the existing request,
response, and rate limits. Another owner's or missing proposal gets the same
404. Stale or ineligible proposals get a 409 with no state change. The browser
must show the pending snapshot and an explicit confirmation control; a preview
or save action cannot approve it. On retry, the same proposal returns the same
version, even after a later version supersedes it.

Read views must distinguish pending, active, and superseded truthfully. This
boundary does not make a daily calorie target a complete plan or authorize
automatic meal selection, exercise prescription, or clinical guidance.
