# Weight Goal Increment

A recorded goal expresses user intent: gain, lose, or maintain weight. It does
not prescribe a medically suitable target, generate workouts or calorie targets,
estimate muscle gain, or promise an outcome or completion date.

## Plain rules

Gain requires a target above the starting weight. Loss requires a target below
it. Maintenance has no target weight. Equal gain/loss targets, missing targets,
unsupported directions, booleans, numeric strings, and non-finite numbers are
rejected. Starting and target weights use the profile's supported application
range of 20–500 kg; this is not a medical reference range or approval of a target.

The plain Python service returns immutable GoalDetails values. Starting weight
will come from the authenticated user's saved profile, not from browser input.
It is a snapshot for the saved goal; later profile edits must not rewrite it.
Repeated saves of the same direction/target must preserve that snapshot.
Changing the goal intentionally will use the profile weight at that save.

This feature is one onboarding step. Goals and the four basic profile fields
alone remain insufficient to produce a personalized workout or nutrition plan.

## Persistence and retries

Migration 0003 creates one current goal per saved profile. The authenticated
profile's weight is read under a row lock, serializing goal saves and profile
edits. Identical direction/target retries preserve the stored starting weight,
even if a later profile edit crosses the target. An intentional change uses
the current profile weight. This records intent only; goal progress or completion
is not inferred. Concurrent identical saves produce one row. SQL constraints
reject missing gain/loss targets, invalid directions, inconsistent target weights,
and goals without an owning profile. No goal history is implemented yet.

## Protected API

GET /api/goal reads only the authenticated owner's goal; absent goals return 404.
PUT /api/goal accepts only direction and optional target_weight_kg, with the
shared session/origin guards, a 2048-byte body cap, strict schema validation,
and existing time/rate/response limits. The owner and starting weight are always
selected by the server. A missing profile returns 409; invalid changes return 422
and preserve the saved goal. Responses expose only direction, starting_weight_kg,
and target_weight_kg. No plan, progress, or completion date is returned.

## Browser flow

/goal redirects anonymous visitors to sign-in and accounts without a profile to
/profile. The responsive form supports gain, loss, and maintenance. Maintenance
hides and disables the target input; edits clear stale success feedback. All
messages use textContent and requests have a timeout and duplicate-submit guard.
No weights are placed in URLs. Successful saves reload server-rendered values.

Browser checks used only synthetic data in the disposable cluster: profile-first
onboarding, invalid gain rejection, valid gain save, saved-value reload, profile
weight changes without snapshot rewriting, identical-save stability, maintenance
without a target, and mobile layout without horizontal overflow.
