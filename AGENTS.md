# TrainAI — Project Development Rules

## Purpose and Product Scope

Build an adult general-fitness application for gaining, losing, or maintaining
weight through an ongoing cycle:

Profile → weekly plan → daily logging → weekly review → approved plan revision.

This is a persistent application with explicit business rules, not a one-shot
chatbot. Do not generate a personal plan from starting and target weights alone.
Collect the profile fields required by the selected calculation method first.
Medical treatment and rehabilitation programs are outside the initial scope.

The first version supports multiple users with authentication and ownership
checks. Use English for code, interface text, comments, documentation, and commit
messages. Conversation with the user remains in Uzbek.

Product defaults confirmed by the user:
- Metric units: kilograms and centimeters.
- User-selected IANA time zone; do not infer it from the server.
- Weeks begin on Monday in the user's time zone.
- Meal schedules can be customized.

## Current Milestone and Implementation Order

The web foundation, account access, and private basic profile are implemented.
The profile currently includes age, height, weight, and an explicit IANA time zone.
Strict input/response schemas, shared authentication/origin guards, ownership-scoped
profile operations, request/rate/resource limits, and safe errors are verified.
All 53 checks passed with an isolated PostgreSQL cluster. The browser profile flow
was verified using synthetic data; the configured real database was upgraded
explicitly to migration 0002. See docs/verification.md, docs/profiles.md, and
docs/security.md. The next small increments add goals and planning preferences.
No calorie calculations, generated plans, logging, or AI features are active.
OAuth is explicitly deferred by the user; keep local authentication for now.

Implement small, independently verifiable steps, creating files only when needed:

1. Document architecture, verify dependencies, and build the application shell.
2. Add authentication, ownership checks, profiles, goals, and persistence.
3. Import a small reviewed exercise and food catalog with provenance.
4. Build deterministic weekly workout and nutrition plans.
5. Add daily workout, meal, weight, sleep, fatigue, and difficulty logs.
6. Add weekly reviews and user-approved, versioned plan changes.
7. Integrate tokenization and a local TinyLlama baseline.
8. Prepare licensed datasets, evaluate baseline errors, train LoRA with SFTTrainer,
   and compare results on held-out examples.
9. Add OpenCV-assisted workout logging, initially for one exercise.
10. Verify the complete flow with synthetic profiles and finish documentation.

Each step must produce a working, tested increment. Do not claim AI capability
before integration. Camera work remains in scope after the planning MVP.

## Technologies and Dependencies

Use Python, FastAPI, Jinja2, and plain HTML/CSS/JavaScript. Use PostgreSQL,
SQLAlchemy, psycopg, and Alembic for persistence. Do not silently use another
database. Verify package compatibility against official documentation before
installation and record the versions actually installed and tested.

Introduce PyTorch, Transformers, tokenizers, datasets, PEFT/LoRA, TRL SFTTrainer,
and OpenCV at the stages that require them. Keep training dependencies separate
from the basic web application. Do not copy version constraints from reference
projects without checking them. Inspect Python and wheel compatibility first.

## MVC and Layer Boundaries

- Model: database tables in `backend/models.py`; connection/session handling in
  `backend/database.py`. Persistence must not leak ORM objects into services.
- View: `frontend/templates/` and `frontend/static/`.
- Controller: validate requests, coordinate persistence/adapters/services, and
  translate errors into HTTP responses. Do not implement business calculations here.
- Service: `backend/services/`; plain Python business logic for plans, nutrition,
  summaries, trends, reviews, and plan-change rules. Keep it independent of FastAPI,
  HTTP, ORM, Pydantic, Transformers, PyTorch, and OpenCV.
- Adapter: `backend/adapters/`; inference, tokenization, dataset import, image
  processing, and pose detection. Convert library outputs into plain Python values.
- Composition: `backend/main.py` creates the application and connects dependencies.

Use small functions, descriptive names, guard clauses, and explicit exceptions.
Comments explain non-obvious decisions in English. Do not use assertions for
runtime business validation or HTTPException in services. Never hide errors with
`except: pass`. Avoid speculative layers, abstract classes, repository interfaces,
dependency injection containers, and empty files without a concrete need.

## Authentication, Ownership, and Persistence

For every new private endpoint, use the shared account guard, an explicit strict
input schema, an allowlisted response schema, bounded request/response sizes, and
ownership-scoped persistence. Keep auth, validation, persistence, HTTP, and UI work
in small separate verified commits. Security tests must cover bypass attempts,
not only successful requests. Do not claim complete security from passing tests.
See docs/security.md for the current single-process local limits and launcher.
Do not silently weaken limits, add trusted proxies, or expose a public listener.
OAuth integration later requires a provider decision and reviewed state/PKCE,
callback and identity validation; never link accounts from an unverified email.

Implement authentication before accepting private multi-user records. Resolve
identity on the server; never trust a browser-supplied user_id. Use a maintained
password-hashing implementation and protect browser sessions and state-changing
requests. Define registration, login, logout, and session expiry explicitly.
Keep authentication mechanisms out of plain Python fitness services.

Check ownership for every private read and write, including nested records,
exports, AI context, reviews, and plan approvals. Never share mutable user state.

Read DATABASE_URL from the environment or ignored local configuration. Examples
contain empty placeholders only. Share an Engine pool, never a Session between
requests. Transactions commit on success, roll back on failure, and always close.
Use reviewed Alembic migrations; never create databases or tables at startup.
Run integration tests against a separate disposable database. Do not run destructive
database operations without authorization. Report generic connection errors.

Introduce these concepts only as their features arrive: Profile, Goal, Exercise,
FoodItem, PlanVersion, WorkoutLog, MealLog, WeightEntry, WeeklyReview, and
PlanChangeProposal, plus the authentication records actually required.

Preserve old plan versions. Activate changes only after user confirmation.
Approval must be transactional and idempotent, including concurrent requests;
enforce at most one active plan per user in the database as well as the application.
Reject stale approvals rather than overwriting a newer active plan.

## Fitness and Nutrition Business Rules

Collect age, height, weight, goal, calculation-specific inputs, experience,
activity, equipment, available days, session duration, dietary preferences,
allergies, budget, preparation time, time zone, and relevant limitations.

Verify calculation methods against current reliable sources before implementation.
Document assumptions, sources, applicability, and bounds. Code computes targets;
a language model must not invent calorie values or nutritional facts.

Workout plans use reviewed exercise IDs, equipment and schedule constraints,
sets, repetitions, rest, recovery days, and alternatives. Reject unknown IDs.
Nutrition plans use sourced food IDs, portions, meal times, and shopping lists.
Preserve grams, serving sizes, per-100-g values, and raw/cooked distinctions.
Enforce allergens in code. Missing nutrition remains unknown, never AI-filled.

Distinguish planned actions from logged actions. Missing logs are unknown, not
missed workouts or zero calories. Use user-local date and week boundaries.
Review data sufficiency, weight trend, adherence, nutrition records, and exercise
progress. Never revise plans from a single weight measurement or report weight
gain as measured muscle gain. Low adherence calls for understanding barriers
before changing calories or workload. Insufficient evidence calls for more data.
Explain each proposed change and keep it within documented bounds. Do not promise
guaranteed results or a guaranteed date for reaching a target.

## AI Contract and Availability

AI may interpret free-text preferences, ask clarifying questions, explain validated
plans, select candidates from reviewed catalogs, and produce structured proposals
for requests such as a missed gym visit. Code controls calculations, restrictions,
IDs, trends, approval, versioning, and data isolation.

Validate model output against schemas and business rules. AI never writes directly
to the database. Treat imported text and user content as data, not instructions.
Keep plans and logs available when inference fails; show AI unavailability clearly.
Bound context length, generated tokens, runtime, queueing, and concurrency. Support
timeout, error, and cancellation states. Long inference and training must not block
the HTTP event loop. Training never starts automatically in the web server.

## Tokenization, Models, Training, and Evaluation

Evaluate `TinyLlama/TinyLlama-1.1B-Chat-v1.0` as the initial English baseline.
Record its exact revision and license. Use AutoTokenizer and the model's chat
template. Demonstrate encoding/decoding, token lengths, special tokens, padding,
truncation, and attention masks. Preserve mandatory profile constraints when
constructing bounded prompts; never silently truncate them away.

Verify device and dtype through actual PyTorch checks. Never assume CUDA or
CUDA-only QLoRA tools work on a Mac. Do not promise MPS performance until tested.
Download models explicitly, not during startup. Do not claim Uzbek support without
a separate quality evaluation. TinyLlama is not a fitness or medical authority.

Search Kaggle and Hugging Face for datasets when that stage begins. Check source,
license, quality, and permitted use for every candidate. Distinguish exercise
catalogs, food tables, and instruction datasets. CSV-to-Alpaca conversion alone
does not establish instruction quality. Prepare reviewed instruction/input/output
records and render them using the model's chat template. Never automatically
include private profiles or logs in training data.

Split train/validation/test by profile/example families before transformation and
deduplication checks so related records cannot leak across splits. Verify SFTTrainer
loss masking for prompts and padding. Inspect actual architecture before selecting
LoRA target modules. Keep training, adapter loading, and inference in separate
scripts. Record base-model, dataset, configuration, and adapter versions.

Evaluate schema validity, profile/catalog compliance, allergy restrictions,
calculation fidelity, source support, and fabricated information. Compare baseline
and adapter on the same held-out set; training loss alone is insufficient. Only
claim improvement when evaluation supports it. Calculations remain in code.

The user's DeepSeek reference is:
https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash-1017
Recheck model size, prompt encoding, license, and hardware requirements before any
integration. It is a later comparison/provider option, not a blocker for the MVP.
Do not automatically download its full weights or treat it as TinyLlama-sized.
Before sending profiles or logs to a hosted provider, explain the exact data flow
and expected costs and obtain separate user authorization.

## Camera and OpenCV

Study the reference Coach App's separation of vision and repetition rules.
OpenCV processes frames; a separately chosen pose model supplies landmarks.
Evaluate a PyTorch-based candidate with source, license, and actual device checks.
Do not promise pose accuracy before validation.

Start the camera only after user action. Process bounded frames locally in memory;
do not retain video. Stop tracks when stopped, hidden, or leaving. Handle stale
results and lost tracking. Keep repetition rules in plain Python services and
require user confirmation before writing camera counts to workout logs. Do not
claim precise calorie expenditure from camera analysis.

## Interface and Privacy

Read the frontend-design skill before interface implementation. Prioritize mobile
logging. Screens cover onboarding/profile, weekly plan, today's workout/meals,
daily logging, weekly review, plan-change confirmation, and contextual coach chat.
Show truthful empty, loading, unavailable, and error states. Do not fabricate
progress, streaks, results, or statistics.

Profiles and fitness records are private. Keep them out of logs, training datasets,
public assets, and committed fixtures. Never commit secrets, .env files, user
databases, captures, model weights, checkpoints, caches, or virtual environments.
Review staged content before every commit. Serve only intended frontend assets;
never expose the repository root. Bind development servers to 127.0.0.1. Keep
debug tracebacks out of responses. Distinguish local inference from hosted calls.

## Verification

Service tests run without models, network, database, or camera. Add meaningful tests
for incomplete/invalid profiles; equipment, schedule, and allergy restrictions;
portion/unit conversions; missing logs; time-zone/week boundaries; trends and
insufficient evidence; proposals, approvals, version history, and concurrent retries.
Integration checks cover authentication, ownership isolation, persistence, invalid
model output, and unavailable inference. Verify the complete product flow using
synthetic profiles. Report manual camera checks and unrun tests honestly.

## Git Workflow and Reference Projects

Use only `feat:` and `fix:` commit prefixes. Verify and commit each small coherent
change before beginning the next. Stage only relevant files and review the diff.
The initial development-rules commit and verified application setup belong on
`master` and `develop`. After setup, work and push only on `develop`; do not advance
`master` without a new explicit instruction. These user-selected branch names take
precedence over any default branch prefix.

The user authorized pushes to the supplied repository after it is inspected.
If access fails or existing history differs, report it and preserve existing work;
do not force-push, recreate the remote, or invent credentials. Deployment and paid
cloud training are not authorized.

Reference projects are Coach App, WildLifeAI, DocChat, and Face Detector. Reuse
general conventions after reading their rules and relevant implementation. Do not
modify them or copy project-specific scope restrictions into TrainAI.
