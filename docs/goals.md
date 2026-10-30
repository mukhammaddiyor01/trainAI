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
